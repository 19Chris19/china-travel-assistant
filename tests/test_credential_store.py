import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from china_travel_assistant.credential_store import profile_status, run_with_profile


class CredentialStoreTests(unittest.TestCase):
    def test_profile_status_reports_only_public_state(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "src" / "profile.ts"
            script.parent.mkdir()
            script.write_text("fixture", encoding="utf-8")
            with (
                patch.dict(os.environ, {"CHINA_TRAVEL_CREDENTIAL_UI": directory}, clear=True),
                patch("china_travel_assistant.credential_store.shutil.which", return_value="node"),
                patch("china_travel_assistant.credential_store.subprocess.run",
                      return_value=SimpleNamespace(returncode=0, stdout='{"configured":true}')),
            ):
                self.assertEqual(profile_status("amap"), "ready")
            with (
                patch.dict(os.environ, {"CHINA_TRAVEL_CREDENTIAL_UI": directory}, clear=True),
                patch("china_travel_assistant.credential_store.shutil.which", return_value=None),
            ):
                self.assertEqual(profile_status("amap"), "missing")

    def test_profile_run_injects_only_selected_provider_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "src" / "profile.ts"
            script.parent.mkdir()
            script.write_text("fixture", encoding="utf-8")
            environment = {
                "CHINA_TRAVEL_CREDENTIAL_UI": directory,
                "AMAP_WEBSERVICE_KEY": "fake-amap",
                "FLYAI_API_KEY": "fake-flyai",
                "VARIFLIGHT_API_KEY": "fake-vari",
                "QWEATHER_PRIVATE_KEY_PATH": "/fake/private.pem",
                "PATH": os.environ.get("PATH", ""),
            }
            with (
                patch.dict(os.environ, environment, clear=True),
                patch("china_travel_assistant.credential_store.shutil.which", return_value="node"),
                patch("china_travel_assistant.credential_store.subprocess.run",
                      return_value=SimpleNamespace(returncode=0)) as run,
            ):
                self.assertEqual(run_with_profile("flyai", ["flyai", "search"]), 0)
        passed = run.call_args.kwargs["env"]
        self.assertEqual(passed["FLYAI_API_KEY"], "fake-flyai")
        self.assertNotIn("AMAP_WEBSERVICE_KEY", passed)
        self.assertNotIn("VARIFLIGHT_API_KEY", passed)
        self.assertNotIn("QWEATHER_PRIVATE_KEY_PATH", passed)


if __name__ == "__main__":
    unittest.main()
