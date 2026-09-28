"""Use the fixed local credential page without returning secret values to the Agent."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROVIDER_VARIABLES = {
    "amap": "AMAP_WEBSERVICE_KEY",
    "flyai": "FLYAI_API_KEY",
    "variflight": "VARIFLIGHT_API_KEY",
}


def credential_ui_root() -> Path:
    configured = os.environ.get("CHINA_TRAVEL_CREDENTIAL_UI")
    if configured:
        return Path(configured).expanduser()
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_home / "china-travel-assistant" / "credential-ui"


def profile_status(provider: str) -> str:
    """Return only a public state; never return a credential reference or value."""
    if provider not in PROVIDER_VARIABLES:
        raise ValueError("unsupported provider profile")
    if os.environ.get(PROVIDER_VARIABLES[provider]):
        return "ready"
    node = shutil.which("node")
    script = credential_ui_root() / "src" / "profile.ts"
    if not node or not script.is_file():
        return "missing"
    try:
        result = subprocess.run(
            [node, str(script), "status", provider],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
        payload = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return "degraded"
    if result.returncode == 0 and payload.get("configured") is True:
        return "ready"
    if result.returncode == 2 and payload.get("configured") is False:
        return "missing"
    return "degraded"


def run_with_profile(provider: str, command: list[str]) -> int:
    if provider not in PROVIDER_VARIABLES:
        raise ValueError("unsupported provider profile")
    node = shutil.which("node")
    script = credential_ui_root() / "src" / "profile.ts"
    if not node or not script.is_file():
        raise RuntimeError("system credential page unavailable; install optional credential support")
    environment = os.environ.copy()
    for name in PROVIDER_VARIABLES.values():
        if name != PROVIDER_VARIABLES[provider]:
            environment.pop(name, None)
    for name in ("AMAP_JSAPI_KEY", "AMAP_SECURITY_CODE", "VIGOLIVE_API_KEY"):
        environment.pop(name, None)
    return subprocess.run(
        [node, str(script), "run", provider, "--", *command], env=environment, check=False,
    ).returncode


def reenter_with_profile(provider: str, argv: list[str]) -> int:
    return run_with_profile(provider, [sys.executable, "-m", "china_travel_assistant.cli", *argv])
