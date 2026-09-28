from __future__ import annotations

import base64
import json
import os
import stat
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from .contracts import CHINA_TIMEZONE, RiskLevel, WeatherRisk


QWEATHER_ENV_KEYS = (
    "QWEATHER_API_HOST",
    "QWEATHER_KEY_ID",
    "QWEATHER_DEVELOPER_ID",
    "QWEATHER_PROJECT_ID",
    "QWEATHER_PRIVATE_KEY_PATH",
)


class QWeatherConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class QWeatherCredentials:
    api_host: str
    key_id: str
    developer_id: str
    project_id: str
    private_key_path: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "QWeatherCredentials":
        missing = [key for key in QWEATHER_ENV_KEYS if not str(values.get(key) or "").strip()]
        if missing:
            raise QWeatherConfigurationError(f"missing QWeather settings: {', '.join(missing)}")
        host = str(values["QWEATHER_API_HOST"]).strip().rstrip("/")
        parsed = urlsplit(host)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise QWeatherConfigurationError("QWEATHER_API_HOST must be an https API host without a query")
        return cls(
            api_host=host,
            key_id=str(values["QWEATHER_KEY_ID"]).strip(),
            developer_id=str(values["QWEATHER_DEVELOPER_ID"]).strip(),
            project_id=str(values["QWEATHER_PROJECT_ID"]).strip(),
            private_key_path=os.path.expanduser(str(values["QWEATHER_PRIVATE_KEY_PATH"]).strip()),
        )

    @property
    def private_key_is_secure(self) -> bool:
        try:
            mode = stat.S_IMODE(os.stat(self.private_key_path).st_mode)
        except OSError:
            return False
        return mode & 0o077 == 0

    def status(self) -> str:
        if not os.path.isfile(self.private_key_path):
            return "missing_private_key"
        if not self.private_key_is_secure:
            return "insecure_private_key_permissions"
        return "configured"


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_jwt(
    credentials: QWeatherCredentials,
    *,
    now: int | None = None,
    signer: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> str:
    """Sign a short-lived JWT locally; neither the key nor token is persisted."""

    if credentials.status() != "configured":
        raise QWeatherConfigurationError(credentials.status())
    issued_at = (now if now is not None else int(time.time())) - 30
    header = _base64url(json.dumps({"alg": "EdDSA", "kid": credentials.key_id}, separators=(",", ":")).encode())
    payload = _base64url(
        json.dumps(
            {
                "iss": credentials.developer_id,
                "sub": credentials.project_id,
                "iat": issued_at,
                "exp": issued_at + 900,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    completed = signer(
        ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", credentials.private_key_path],
        input=signing_input,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise QWeatherConfigurationError("unable to sign QWeather JWT with the configured private key")
    return f"{header}.{payload}.{_base64url(completed.stdout)}"


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _risk_level(
    *, precipitation_probability: int | None, precipitation_mm: float | None, wind_kph: float | None,
    visibility_km: float | None, alert_summary: str | None,
) -> RiskLevel:
    if alert_summary or (visibility_km is not None and visibility_km < 1) or (wind_kph is not None and wind_kph >= 50):
        return RiskLevel.CHALLENGE
    if (
        (precipitation_probability is not None and precipitation_probability >= 60)
        or (precipitation_mm is not None and precipitation_mm >= 5)
        or (visibility_km is not None and visibility_km < 3)
        or (wind_kph is not None and wind_kph >= 30)
    ):
        return RiskLevel.MANAGED
    return RiskLevel.STABLE


def weather_risk_from_payload(location: str, payload: Mapping[str, Any], *, queried_at: datetime | None = None) -> WeatherRisk:
    """Normalize only reported weather fields; omitted provider fields remain null."""

    now = payload.get("now") if isinstance(payload.get("now"), Mapping) else payload
    probability = now.get("precipProbability") if isinstance(now, Mapping) else None
    try:
        probability_value = int(probability) if probability not in (None, "") else None
    except (TypeError, ValueError):
        probability_value = None
    if probability_value is not None and not 0 <= probability_value <= 100:
        probability_value = None
    precipitation = _number(now.get("precip") if isinstance(now, Mapping) else None)
    wind_kph = _number(now.get("windSpeed") if isinstance(now, Mapping) else None)
    visibility = _number(now.get("vis") if isinstance(now, Mapping) else None)
    alert = now.get("alert") if isinstance(now, Mapping) else None
    alert_summary = str(alert).strip() if alert not in (None, "") else None
    risk = _risk_level(
        precipitation_probability=probability_value,
        precipitation_mm=precipitation,
        wind_kph=wind_kph,
        visibility_km=visibility,
        alert_summary=alert_summary,
    )
    recommendation = {
        RiskLevel.STABLE: "Weather signals do not add a routing buffer beyond the normal transfer policy.",
        RiskLevel.MANAGED: "Add transfer buffer and keep an indoor or later-departure alternative.",
        RiskLevel.CHALLENGE: "Avoid tight outdoor connections until the alert, wind, or visibility condition clears.",
    }[risk]
    return WeatherRisk(
        location=location,
        observed_at=queried_at or datetime.now(CHINA_TIMEZONE),
        precipitation_probability=probability_value,
        precipitation_mm=precipitation,
        wind_kph=wind_kph,
        visibility_km=visibility,
        alert_summary=alert_summary,
        risk_level=risk,
        recommendation=recommendation,
    )


def probe_qweather(credentials: QWeatherCredentials) -> None:
    token = build_jwt(credentials)
    url = urljoin(f"{credentials.api_host}/", "weather/v1/now/101010100")
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping) or not isinstance(payload.get("now"), Mapping):
        raise QWeatherConfigurationError("QWeather returned an unexpected payload")
