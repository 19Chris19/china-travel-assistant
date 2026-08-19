import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from china_travel_assistant.cli import main


class CliTests(unittest.TestCase):
    def test_normalize_request_rejects_non_object_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(["normalize-request", "[]"])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("JSON object", stderr.getvalue())

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
            patch(
                "china_travel_assistant.cli.load_credentials",
                return_value={"AMAP_WEBSERVICE_KEY": "file-key"},
            ),
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
            patch(
                "china_travel_assistant.cli.load_credentials",
                return_value={
                    "FLYAI_API_KEY": "file-key",
                    "AMAP_WEBSERVICE_KEY": "no-amap",
                },
            ),
            patch("china_travel_assistant.cli.shutil.which", return_value="/usr/bin/flyai"),
            patch("china_travel_assistant.cli.subprocess.run", return_value=completed) as run,
            patch.dict(
                os.environ,
                {
                    "PATH": os.environ.get("PATH", ""),
                    "AMAP_WEBSERVICE_KEY": "inherited-amap",
                    "VARIFLIGHT_API_KEY": "inherited-vari",
                    "VIGOLIVE_API_KEY": "inherited-vigo",
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
