from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .contracts import ProviderHealth


DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "china-travel-assistant" / "credentials.env"
RAIL_REVISION = "1b6ee94ff801cbfe0c1e8c8bb95195466b08b6dd"


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


def load_credentials(path: Path = DEFAULT_CREDENTIALS_PATH) -> dict[str, str]:
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
            values[key.strip()] = value.strip().strip("'\"")
    for key in (
        "AMAP_WEBSERVICE_KEY",
        "AMAP_JSAPI_KEY",
        "AMAP_SECURITY_CODE",
        "FLYAI_API_KEY",
        "VARIFLIGHT_API_KEY",
        "VIGOLIVE_API_KEY",
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


class Doctor:
    def __init__(
        self,
        *,
        live: bool = False,
        credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
        probes: Mapping[str, Callable[[str | None], object]] | None = None,
    ) -> None:
        self.live = live
        self.credentials_path = credentials_path
        self.probes = dict({"amap": probe_amap, "variflight": probe_variflight} if probes is None else probes)

    def run(self) -> dict[str, dict[str, str]]:
        credentials = load_credentials(self.credentials_path)
        result = {
            "amap": self._provider(
                "amap",
                credentials.get("AMAP_WEBSERVICE_KEY"),
                required=True,
                version="web-service-v3-v5",
            ),
            "flyai": self._binary_provider("flyai", "flyai", required=True),
            "variflight": self._provider(
                "variflight", credentials.get("VARIFLIGHT_API_KEY"), required=False, version="1.0.3"
            ),
            "12306": self._binary_provider(
                "12306", "uvx", required=True, unverified=True, version=f"git:{RAIL_REVISION}"
            ),
            "ego-browser": {
                **self._binary_provider("ego-browser", "ego-browser", required=False),
                "skill_version": "1.2.3",
            },
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return result

    def _provider(
        self, name: str, credential: str | None, *, required: bool, version: str
    ) -> dict[str, str]:
        if not credential:
            return {
                "status": ProviderHealth.MISSING.value,
                "check": "configuration_only",
                "required": str(required).lower(),
                "version": version,
            }
        if not self.live:
            return {
                "status": ProviderHealth.READY.value,
                "check": "configuration_only",
                "required": str(required).lower(),
                "version": version,
            }
        probe = self.probes.get(name)
        if probe is None:
            return {
                "status": ProviderHealth.DEGRADED.value,
                "check": "live_probe_unavailable",
                "required": str(required).lower(),
                "version": version,
            }
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
        return {
            "status": state.value,
            "check": "live",
            "required": str(required).lower(),
            "version": version,
        }

    @staticmethod
    def _binary_provider(
        name: str,
        binary: str,
        *,
        required: bool,
        unverified: bool = False,
        version: str | None = None,
    ) -> dict[str, str]:
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
        return {
            "status": status.value,
            "check": check,
            "required": str(required).lower(),
            "version": detected_version,
        }
