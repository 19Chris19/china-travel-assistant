import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def test_core_installer_rejects_python_39_before_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            bin_dir.mkdir()
            codex = bin_dir / "codex"
            codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            codex.chmod(0o755)
            python = bin_dir / "python3"
            python.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
            python.chmod(0o755)
            result = subprocess.run(
                [str(ROOT / "scripts" / "install-local.sh")],
                env={"HOME": directory, "PATH": f"{bin_dir}:/usr/bin:/bin"},
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Python 3.10+ is required", result.stderr)

    def test_core_installer_does_not_require_optional_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            local_bin = Path(directory) / ".local" / "bin"
            bin_dir.mkdir()
            local_bin.mkdir(parents=True)
            for name in ("codex", "pipx"):
                tool = bin_dir / name
                tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                tool.chmod(0o755)
            python = bin_dir / "python3"
            python.symlink_to(sys.executable)
            result = subprocess.run(
                [str(ROOT / "scripts" / "install-local.sh")],
                env={"HOME": directory, "PATH": f"{bin_dir}:/usr/bin:/bin"},
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Core installed", result.stdout)


if __name__ == "__main__":
    unittest.main()
