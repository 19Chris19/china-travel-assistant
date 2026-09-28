"""Build byte-for-byte reproducible Plugin ZIP and wheel assets."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "china-travel-assistant"
EXCLUDED_PARTS = {"__pycache__", "node_modules", "build", "dist", "evals", "tests"}
SECRET_PATTERN = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|(?:API_KEY|SECRET|TOKEN)=[^\s\r\n]{12,})")


def source_epoch() -> int:
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured is not None:
        return int(configured)
    return int(subprocess.check_output(["git", "log", "-1", "--format=%ct"], cwd=ROOT, text=True).strip())


def plugin_files() -> list[Path]:
    tracked = subprocess.check_output(["git", "ls-files", "-z", "plugins/china-travel-assistant"], cwd=ROOT)
    files = []
    for raw in tracked.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts):
            continue
        if relative.name in {"credentials.env", ".env", "settings.env"} or relative.suffix == ".pyc":
            continue
        if (ROOT / relative).is_file():
            files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def build_zip(path: Path, epoch: int) -> None:
    timestamp = time.gmtime(max(epoch, 315532800))
    stamp = (timestamp.tm_year, timestamp.tm_mon, timestamp.tm_mday,
             timestamp.tm_hour, timestamp.tm_min, timestamp.tm_sec)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in plugin_files():
            content = (ROOT / relative).read_bytes()
            if SECRET_PATTERN.search(content):
                raise ValueError(f"release asset contains a secret-like value: {relative}")
            name = relative.relative_to("plugins").as_posix()
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(ROOT / relative, os.X_OK) else 0o644) << 16
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_once(directory: Path, version: str, epoch: int) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    zip_path = directory / f"china-travel-assistant-plugin-v{version}.zip"
    build_zip(zip_path, epoch)
    environment = {**os.environ, "SOURCE_DATE_EPOCH": str(epoch), "PYTHONHASHSEED": "0"}
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(directory), str(PLUGIN)],
        cwd=ROOT, env=environment, check=True,
    )
    wheels = list(directory.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("expected exactly one wheel")
    with zipfile.ZipFile(wheels[0]) as wheel:
        for name in wheel.namelist():
            parts = Path(name).parts
            if any(part in EXCLUDED_PARTS for part in parts) or name.endswith((".pyc", "credentials.env")):
                raise ValueError(f"wheel contains excluded content: {name}")
            if SECRET_PATTERN.search(wheel.read(name)):
                raise ValueError(f"wheel contains a secret-like value: {name}")
    return [zip_path, wheels[0]]


def hashes(files: list[Path]) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        parser.error("version must be X.Y.Z")
    epoch = source_epoch()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        source = build_once(Path(first), args.version, epoch)
        duplicate = build_once(Path(second), args.version, epoch)
        checksums = hashes(source)
        if checksums != hashes(duplicate):
            raise RuntimeError("independent release builds are not reproducible")
        args.output.mkdir(parents=True, exist_ok=True)
        for path in source:
            shutil.copy2(path, args.output / path.name)
        lines = [f"{digest}  {name}" for name, digest in sorted(checksums.items())]
        (args.output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii")
    print("Release assets reproducible: " + ", ".join(sorted(checksums)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
