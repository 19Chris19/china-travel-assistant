import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from china_travel_assistant.cli import main


class CliTests(unittest.TestCase):
    def test_plan_cli_accepts_chinese_tier_alias(self):
        payload = {"request": {"origin": "沈阳", "destination": "苏州", "date_start": "2026-08-31"}}
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["plan", json.dumps(payload, ensure_ascii=False), "--tier", "从容"]), 0)
        self.assertEqual(json.loads(output.getvalue())["resolved_tier"], "standard")

    def test_plan_emits_resolved_tier_search_plan_and_itineraries(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(
                [
                    "plan",
                    json.dumps(
                        {
                            "request": {
                                "origin": "沈阳",
                                "destination": "苏州",
                                "date_start": "2026-08-30",
                                "student_fare": True,
                            },
                            "legs": [
                                {
                                    "leg_id": "g1",
                                    "mode": "train",
                                    "origin": "沈阳",
                                    "destination": "苏州",
                                    "provider": "12306",
                                    "duration_minutes": 600,
                                    "total_price_cny": 730,
                                }
                            ],
                        }
                    ),
                    "--presentation",
                    "html",
                ]
            )

        self.assertEqual(result, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["resolved_tier"], "pro")
        self.assertEqual(payload["presentation_requested"], "html")
        self.assertTrue(payload["search_plan"])
        self.assertTrue(payload["itineraries"][0]["is_baseline"])

    def test_normalize_request_rejects_non_object_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(["normalize-request", "[]"])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("JSON object", stderr.getvalue())

    def test_plan_normalizes_multisource_facts_and_rejects_invalid_fact_arrays(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(
                [
                    "plan",
                    json.dumps(
                        {
                            "origin": "无机场城市",
                            "destination": "目的地",
                            "date_start": "2026-09-28",
                            "gateway_candidates": [
                                {
                                    "gateway_id": "a",
                                    "name": "门户 A",
                                    "gateway_type": "airport",
                                    "origin": "无机场城市",
                                    "destination": "目的地",
                                    "flight_total_cny": 500,
                                    "ground_access": [{"endpoint": "门户 A", "mode": "rail", "cost_cny": 20}],
                                }
                            ],
                            "provider_health": [
                                {"provider": "amap", "status": "ready", "capabilities": ["transfer"]}
                            ],
                        }
                    ),
                ]
            )

        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["gateway_candidates"][0]["total_known_cost_cny"], 520)
        self.assertEqual(payload["provider_health"][0]["provider"], "amap")

    def test_rank_offers_rejects_non_array_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(["rank-offers", "{}"])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("JSON array", stderr.getvalue())

    def test_rank_offers_rejects_non_object_array_elements(self):
        for payload in ("[null]", "[1]", "[[]]"):
            with self.subTest(payload=payload):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = main(["rank-offers", payload])

                self.assertEqual(result, 2)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn("offer 0 must be a JSON object", stderr.getvalue())

    def test_amap_route_accepts_coordinates_and_city_context(self):
        output = io.StringIO()
        with (
            patch("china_travel_assistant.cli.AmapClient") as client,
            patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "file-key"}),
            redirect_stdout(output),
        ):
            client.return_value.route.return_value = [{"mode": "transit"}]
            result = main(
                [
                    "amap-route",
                    "transit",
                    "--origin",
                    "121.8,31.15",
                    "--destination",
                    "120.73,31.27",
                    "--city",
                    "上海",
                    "--destination-city",
                    "苏州",
                ]
            )

        self.assertEqual(result, 0)
        client.assert_called_once_with(api_key="file-key")
        client.return_value.route.assert_called_once_with(
            (121.8, 31.15),
            (120.73, 31.27),
            mode="transit",
            city="上海",
            destination_city="苏州",
        )
        self.assertIn('"mode": "transit"', output.getvalue())

    def test_flyai_wrapper_injects_unified_credentials(self):
        completed = type("Completed", (), {"returncode": 0})()
        with (
            patch("china_travel_assistant.cli.shutil.which", return_value="/usr/bin/flyai"),
            patch("china_travel_assistant.cli.subprocess.run", return_value=completed) as run,
            patch.dict(
                os.environ,
                {
                    "PATH": os.environ.get("PATH", ""),
                    "AMAP_WEBSERVICE_KEY": "inherited-amap",
                    "VARIFLIGHT_API_KEY": "inherited-vari",
                    "VIGOLIVE_API_KEY": "inherited-vigo",
                    "FLYAI_API_KEY": "file-key",
                },
                clear=True,
            ),
        ):
            result = main(["flyai", "search-flight", "--origin", "沈阳"])

        self.assertEqual(result, 0)
        command, = run.call_args.args
        self.assertEqual(command, ["flyai", "search-flight", "--origin", "沈阳"])
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["FLYAI_API_KEY"], "file-key")
        self.assertNotIn("AMAP_WEBSERVICE_KEY", environment)
        self.assertNotIn("VARIFLIGHT_API_KEY", environment)
        self.assertNotIn("VIGOLIVE_API_KEY", environment)
        self.assertEqual(environment.get("PATH"), os.environ.get("PATH"))

    def test_flyai_wrapper_reports_missing_binary_without_traceback(self):
        stderr = io.StringIO()
        with (
            patch("china_travel_assistant.cli.shutil.which", return_value=None),
            redirect_stderr(stderr),
        ):
            result = main(["flyai", "search-flight"])

        self.assertEqual(result, 2)
        self.assertIn("flyai binary is not available", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
