from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .credential_store import profile_status, reenter_with_profile
from .contracts import ProviderHealth
from .qweather import QWEATHER_ENV_KEYS, QWeatherConfigurationError, QWeatherCredentials, probe_qweather


RAIL_REVISION = "1b6ee94ff801cbfe0c1e8c8bb95195466b08b6dd"
EGO_SKILL_PATHS = (
    Path.home() / ".agents" / "skills" / "ego-browser" / "SKILL.md",
    Path.home() / ".codex" / "skills" / "ego-browser" / "SKILL.md",
)


class ProviderProbeError(RuntimeError):
    def __init__(self, health: ProviderHealth) -> None:
        super().__init__(health.value)
        self.health = health


def _probe_response(request: Request) -> object:
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 401:
            health = ProviderHealth.EXPIRED
        elif exc.code == 403:
            health = ProviderHealth.FORBIDDEN
        elif exc.code == 429:
            health = ProviderHealth.RATE_LIMITED
        else:
            health = ProviderHealth.DEGRADED
        raise ProviderProbeError(health) from None
    except Exception:
        raise ProviderProbeError(ProviderHealth.DEGRADED) from None


def probe_amap(api_key: str | None) -> None:
    if not api_key:
        raise ProviderProbeError(ProviderHealth.MISSING)
    query = urlencode({"keywords": "北京", "subdistrict": "0", "key": api_key})
    payload = _probe_response(Request(f"https://restapi.amap.com/v3/config/district?{query}"))
    if not isinstance(payload, dict) or payload.get("status") != "1":
        raise ProviderProbeError(ProviderHealth.DEGRADED)


def probe_variflight(api_key: str | None) -> None:
    if not api_key:
        raise ProviderProbeError(ProviderHealth.MISSING)
    body = json.dumps({"endpoint": "getTodayDate", "params": {}}).encode("utf-8")
    request = Request(
        "https://mcp.variflight.com/api/v1/mcp/data",
        data=body,
        headers={"Content-Type": "application/json", "X-VARIFLIGHT-KEY": api_key},
        method="POST",
    )
    payload = _probe_response(request)
    if not isinstance(payload, dict) or payload.get("error"):
        raise ProviderProbeError(ProviderHealth.DEGRADED)


def _default_credentials_path() -> Path:
    config_root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return Path(os.environ.get("CHINA_TRAVEL_SETTINGS_FILE", config_root / "china-travel-assistant" / "settings.env"))


def load_credentials(path: Path | None = None) -> dict[str, str]:
    path = path or _default_credentials_path()
    if path.name == "credentials.env":
        raise ValueError("legacy plaintext credentials are not accepted")
    values: dict[str, str] = {}
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, separator, value = line.partition("=")
            if not separator or not key.strip():
                continue
            if key.strip() in QWEATHER_ENV_KEYS:
                values[key.strip()] = value.strip().strip("'\"")
    for key in (
        "AMAP_WEBSERVICE_KEY",
        "AMAP_JSAPI_KEY",
        "AMAP_SECURITY_CODE",
        "FLYAI_API_KEY",
        "VARIFLIGHT_API_KEY",
        *QWEATHER_ENV_KEYS,
    ):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def _binary_version(binary: str, path: str) -> str:
    resolved = Path(path).resolve()
    if binary == "flyai":
        package_json = resolved.parent.parent / "package.json"
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
            version = payload.get("version")
            return str(version) if version else "unknown"
        except (OSError, ValueError, TypeError):
            return "unknown"

    try:
        completed = subprocess.run(
            [str(resolved), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    first_line = (completed.stdout or completed.stderr).splitlines()
    if not first_line:
        return "unknown"
    parts = first_line[0].strip().split()
    return parts[1] if len(parts) > 1 else parts[0]


def _ego_skill_version(paths: tuple[Path, ...] = EGO_SKILL_PATHS) -> str:
    pattern = re.compile(r'^\s*version:\s*["\']?([^"\'\s]+)', re.MULTILINE)
    for path in paths:
        try:
            match = pattern.search(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if match:
            return match.group(1)
    return "not-installed"


class Doctor:
    def __init__(
        self,
        *,
        live: bool = False,
        credentials_path: Path | None = None,
        probes: Mapping[str, Callable[[object], object]] | None = None,
    ) -> None:
        self.live = live
        self.credentials_path = credentials_path
        self.probes = dict(
            {"amap": probe_amap, "variflight": probe_variflight, "qweather": probe_qweather}
            if probes is None
            else probes
        )

    def run(self) -> dict[str, dict[str, object]]:
        credentials = load_credentials(self.credentials_path)
        result = {
            "amap": self._provider(
                "amap",
                credentials.get("AMAP_WEBSERVICE_KEY"),
                required=True,
                version="web-service-v3-v5",
                capabilities=("poi", "nearby", "transfer", "gateway-discovery"),
            ),
            "flyai": self._flyai_provider(),
            "variflight": self._provider(
                "variflight",
                credentials.get("VARIFLIGHT_API_KEY"),
                required=False,
                version="1.0.3",
                capabilities=("flight-status", "punctuality"),
                absent_status=ProviderHealth.NOT_REQUIRED,
            ),
            "12306": self._binary_provider(
                "12306",
                "uvx",
                required=True,
                unverified=True,
                version=f"git:{RAIL_REVISION}",
                capabilities=("train", "availability"),
            ),
            "qweather": self._qweather_provider(credentials),
            "ego-browser": self._ego_provider(),
            "visualize": self._visualize_provider(),
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return result

    def _provider(
        self,
        name: str,
        credential: object | None,
        *,
        required: bool,
        version: str,
        capabilities: tuple[str, ...] = (),
        absent_status: ProviderHealth = ProviderHealth.MISSING,
    ) -> dict[str, object]:
        if not credential:
            profile_state = profile_status(name)
            if profile_state == "missing":
                return self._health_payload(absent_status, "system_store_status", required, version, capabilities)
            if profile_state == "degraded":
                return self._health_payload(ProviderHealth.DEGRADED, "system_store_status", required, version, capabilities)
            if self.live:
                try:
                    code = reenter_with_profile(name, ["_probe-provider", name])
                except (OSError, RuntimeError):
                    code = 1
                states = {0: ProviderHealth.READY, 3: ProviderHealth.EXPIRED, 4: ProviderHealth.FORBIDDEN,
                          5: ProviderHealth.RATE_LIMITED}
                return self._health_payload(states.get(code, ProviderHealth.DEGRADED), "live", required, version, capabilities)
            return self._health_payload(ProviderHealth.READY, "system_store_status", required, version, capabilities)
        if not self.live:
            return self._health_payload(ProviderHealth.READY, "configuration_only", required, version, capabilities)
        probe = self.probes.get(name)
        if probe is None:
            return self._health_payload(
                ProviderHealth.DEGRADED, "live_probe_unavailable", required, version, capabilities
            )
        try:
            probe(credential)
        except ProviderProbeError as exc:
            state = exc.health
        except PermissionError:
            state = ProviderHealth.FORBIDDEN
        except TimeoutError:
            state = ProviderHealth.RATE_LIMITED
        except Exception:
            state = ProviderHealth.DEGRADED
        else:
            state = ProviderHealth.READY
        return self._health_payload(state, "live", required, version, capabilities)

    @staticmethod
    def _health_payload(
        status: ProviderHealth,
        check: str,
        required: bool,
        version: str,
        capabilities: tuple[str, ...],
    ) -> dict[str, object]:
        return {
            "status": status.value,
            "check": check,
            "required": str(required).lower(),
            "version": version,
            "capabilities": list(capabilities),
            "checked_at": datetime.now().astimezone().isoformat(),
        }

    def _qweather_provider(self, credentials: Mapping[str, str]) -> dict[str, object]:
        capabilities = ("weather", "alerts", "visibility", "outdoor-risk")
        try:
            configured = QWeatherCredentials.from_mapping(credentials)
        except QWeatherConfigurationError as exc:
            state = ProviderHealth.NOT_REQUIRED if "missing QWeather settings" in str(exc) else ProviderHealth.DEGRADED
            return self._health_payload(state, "configuration_only", False, "jwt-ed25519", capabilities)
        status = configured.status()
        if status == "missing_private_key":
            return self._health_payload(ProviderHealth.MISSING, "private_key_presence", False, "jwt-ed25519", capabilities)
        if status != "configured":
            return self._health_payload(ProviderHealth.DEGRADED, status, False, "jwt-ed25519", capabilities)
        return self._provider(
            "qweather", configured, required=False, version="jwt-ed25519", capabilities=capabilities,
            absent_status=ProviderHealth.NOT_REQUIRED,
        )

    @staticmethod
    def _binary_provider(
        name: str,
        binary: str,
        *,
        required: bool,
        unverified: bool = False,
        version: str | None = None,
        capabilities: tuple[str, ...] = (),
    ) -> dict[str, object]:
        path = shutil.which(binary)
        if not path:
            status = ProviderHealth.MISSING
            check = "binary_presence"
            detected_version = version or "not-installed"
        elif unverified:
            status = ProviderHealth.DEGRADED
            check = "runtime_present_server_unverified"
            detected_version = version or _binary_version(binary, path)
        else:
            status = ProviderHealth.READY
            check = "binary_presence"
            detected_version = version or _binary_version(binary, path)
        return Doctor._health_payload(status, check, required, detected_version, capabilities)

    @staticmethod
    def _flyai_provider() -> dict[str, object]:
        result = Doctor._binary_provider(
            "flyai", "flyai", required=False, capabilities=("flight", "hotel", "attractions")
        )
        if result["status"] != ProviderHealth.READY.value:
            return result
        state = profile_status("flyai")
        if state == "missing":
            result["status"] = ProviderHealth.DEGRADED.value
            result["check"] = "binary_present_credential_missing_trial_possible"
        elif state == "degraded":
            result["status"] = ProviderHealth.DEGRADED.value
            result["check"] = "credential_store_unavailable"
        else:
            result["check"] = "binary_and_credential_configuration"
        return result

    @staticmethod
    def _ego_provider() -> dict[str, object]:
        result = Doctor._binary_provider(
            "ego-browser", "ego-browser", required=False, capabilities=("web-verification", "login-handoff")
        )
        skill_version = _ego_skill_version()
        result["skill_version"] = skill_version
        if result["status"] == ProviderHealth.READY.value and skill_version == "not-installed":
            result["status"] = ProviderHealth.DEGRADED.value
            result["check"] = "binary_present_skill_missing"
        return result

    @staticmethod
    def _visualize_provider() -> dict[str, object]:
        return Doctor._health_payload(
            ProviderHealth.UNKNOWN,
            "host_negotiated_at_presentation",
            False,
            "host-provided",
            ("interactive-itinerary",),
        )
