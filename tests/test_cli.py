import io
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
        with patch("china_travel_assistant.cli.AmapClient") as client, redirect_stdout(output):
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
        client.return_value.route.assert_called_once_with(
            (121.8, 31.15),
            (120.73, 31.27),
            mode="transit",
            city="上海",
            destination_city="苏州",
        )
        self.assertIn('"mode": "transit"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
