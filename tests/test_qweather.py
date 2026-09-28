import os
import tempfile
import unittest
from pathlib import Path

from china_travel_assistant.contracts import RiskLevel
from china_travel_assistant.qweather import (
    QWeatherConfigurationError,
    QWeatherCredentials,
    build_jwt,
    weather_risk_from_payload,
)


def settings(path: str) -> dict[str, str]:
    return {
        "QWEATHER_API_HOST": "https://example.qweatherapi.com",
        "QWEATHER_KEY_ID": "credential-id",
        "QWEATHER_DEVELOPER_ID": "Q123456789",
        "QWEATHER_PROJECT_ID": "project-id",
        "QWEATHER_PRIVATE_KEY_PATH": path,
    }


class QWeatherTests(unittest.TestCase):
    def test_configuration_requires_an_https_host_and_a_private_key_with_0600_permissions(self):
        with self.assertRaisesRegex(QWeatherConfigurationError, "missing"):
            QWeatherCredentials.from_mapping({})
        with self.assertRaisesRegex(QWeatherConfigurationError, "https"):
            QWeatherCredentials.from_mapping({**settings("/tmp/key"), "QWEATHER_API_HOST": "http://example.com"})

        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / "private.pem"
            key.write_text("fixture", encoding="utf-8")
            os.chmod(key, 0o600)
            configured = QWeatherCredentials.from_mapping(settings(str(key)))
            self.assertEqual(configured.status(), "configured")
            os.chmod(key, 0o644)
            self.assertEqual(configured.status(), "insecure_private_key_permissions")

    def test_jwt_signing_keeps_key_material_out_of_the_return_value(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / "private.pem"
            key.write_text("not-a-real-private-key", encoding="utf-8")
            os.chmod(key, 0o600)
            credentials = QWeatherCredentials.from_mapping(settings(str(key)))

            def signer(*_args, **_kwargs):
                return type("Completed", (), {"returncode": 0, "stdout": b"signature"})()

            token = build_jwt(credentials, now=100, signer=signer)

        self.assertEqual(len(token.split(".")), 3)
        self.assertNotIn("not-a-real-private-key", token)

    def test_weather_risk_uses_only_reported_signals(self):
        risk = weather_risk_from_payload(
            "机场",
            {"now": {"precipProbability": "70", "windSpeed": "12", "vis": "2", "precip": "0"}},
        )
        unknown = weather_risk_from_payload("机场", {"now": {}})

        self.assertEqual(risk.risk_level, RiskLevel.MANAGED)
        self.assertEqual(unknown.risk_level, RiskLevel.STABLE)
        self.assertIsNone(unknown.visibility_km)
