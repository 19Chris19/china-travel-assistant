import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from china_travel_assistant.doctor import Doctor, load_credentials


class DoctorTests(unittest.TestCase):
    def test_credentials_file_supports_export_and_never_overrides_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.env"
            path.write_text(
                'export AMAP_WEBSERVICE_KEY="from-file"\nVARIFLIGHT_API_KEY=file-key\n',
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "from-env"}, clear=True):
                values = load_credentials(path)

        self.assertEqual(values["AMAP_WEBSERVICE_KEY"], "from-env")
        self.assertEqual(values["VARIFLIGHT_API_KEY"], "file-key")

    def test_default_doctor_does_not_call_live_probes_or_print_secrets(self):
        secret = "secret-value-that-must-not-appear"
        with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": secret}, clear=False):
            doctor = Doctor(live=False, probes={"amap": lambda _: self.fail("probe called")})
            output = io.StringIO()
            with redirect_stdout(output):
                result = doctor.run()

        rendered = output.getvalue()
        self.assertNotIn(secret, rendered)
        self.assertEqual(result["amap"]["status"], "ready")
        self.assertEqual(result["amap"]["check"], "configuration_only")

    def test_live_doctor_maps_probe_errors_without_echoing_payload(self):
        def forbidden(_):
            raise PermissionError("403 token=do-not-print")

        with patch.dict(os.environ, {"VARIFLIGHT_API_KEY": "secret"}, clear=False):
            doctor = Doctor(live=True, probes={"variflight": forbidden})
            output = io.StringIO()
            with redirect_stdout(output):
                result = doctor.run()

        self.assertEqual(result["variflight"]["status"], "forbidden")
        self.assertNotIn("do-not-print", output.getvalue())

    def test_optional_ego_is_not_reported_as_required(self):
        doctor = Doctor(live=False)
        with patch("china_travel_assistant.doctor.shutil.which", return_value=None):
            output = io.StringIO()
            with redirect_stdout(output):
                result = doctor.run()

        self.assertEqual(result["ego-browser"]["required"], "false")

    def test_doctor_reports_provider_and_runtime_versions(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = Doctor(live=False).run()

        for provider in ("amap", "flyai", "variflight", "12306", "ego-browser"):
            self.assertIn("version", result[provider], provider)
        self.assertEqual(result["amap"]["version"], "web-service-v3-v5")
        self.assertEqual(result["variflight"]["version"], "1.0.3")
        self.assertEqual(result["ego-browser"]["skill_version"], "1.2.3")

    def test_12306_configuration_is_not_inferred_from_generic_uvx(self):
        doctor = Doctor(live=False)
        with patch("china_travel_assistant.doctor.shutil.which", return_value="/usr/bin/uvx"):
            output = io.StringIO()
            with redirect_stdout(output):
                result = doctor.run()

        self.assertEqual(result["12306"]["status"], "degraded")
        self.assertEqual(result["12306"]["check"], "runtime_present_server_unverified")

    def test_default_live_probes_make_minimal_amap_and_variflight_requests(self):
        class Response:
            def __init__(self, body):
                self.body = body

            def read(self):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        seen = []

        def opener(request, *, timeout):
            seen.append(request.full_url)
            if "amap.com" in request.full_url:
                return Response(b'{"status":"1","districts":[]}')
            return Response(b'{"data":{"date":"2026-08-19"}}')

        env = {"AMAP_WEBSERVICE_KEY": "amap-secret", "VARIFLIGHT_API_KEY": "vari-secret"}
        with patch.dict(os.environ, env, clear=True), patch("china_travel_assistant.doctor.urlopen", opener):
            output = io.StringIO()
            with redirect_stdout(output):
                result = Doctor(live=True).run()

        self.assertEqual(result["amap"]["status"], "ready")
        self.assertEqual(result["variflight"]["status"], "ready")
        self.assertEqual(len(seen), 2)
        self.assertNotIn("amap-secret", output.getvalue())
        self.assertNotIn("vari-secret", output.getvalue())

    def test_default_live_probe_classifies_http_status(self):
        def opener(request, *, timeout):
            raise HTTPError(request.full_url, 429, "limited", {}, None)

        with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "secret"}, clear=True), patch(
            "china_travel_assistant.doctor.urlopen", opener
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                result = Doctor(live=True).run()

        self.assertEqual(result["amap"]["status"], "rate_limited")
        self.assertNotIn("secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
