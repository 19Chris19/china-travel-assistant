import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "china-travel-assistant"


class PackagingTests(unittest.TestCase):
    def test_marketplace_points_to_the_plugin(self):
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(marketplace["name"], "china-travel-assistant")
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "china-travel-assistant")
        self.assertEqual(entry["source"]["path"], "./plugins/china-travel-assistant")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")

    def test_plugin_manifest_is_public_and_complete(self):
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "china-travel-assistant")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["repository"], "https://github.com/19Chris19/china-travel-assistant")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertEqual(manifest["skills"], "./skills/")

    def test_mcp_config_pins_12306_and_variflight_versions(self):
        config = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        rail_command = " ".join(config["china-12306"]["args"])
        flight_command = " ".join(config["variflight"]["args"])
        self.assertIn("1b6ee94ff801cbfe0c1e8c8bb95195466b08b6dd", rail_command)
        self.assertIn("@variflight-ai/variflight-mcp@1.0.3", flight_command)
        self.assertNotIn("VARIFLIGHT_API_KEY", json.dumps(config["variflight"]))

    def test_credentials_template_has_names_only(self):
        template = (ROOT / ".env.example").read_text(encoding="utf-8")
        expected = {
            "AMAP_WEBSERVICE_KEY",
            "AMAP_JSAPI_KEY",
            "AMAP_SECURITY_CODE",
            "FLYAI_API_KEY",
            "VARIFLIGHT_API_KEY",
            "VIGOLIVE_API_KEY",
        }
        present = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", template, re.MULTILINE))
        self.assertEqual(present, expected)
        for line in template.splitlines():
            if "=" in line and not line.startswith("#"):
                self.assertEqual(line.split("=", 1)[1], "")

    def test_provenance_records_required_relationship_types(self):
        provenance = (ROOT / "provenance.yml").read_text(encoding="utf-8")
        self.assertIn("forked_from", provenance)
        self.assertIn("integrates_with", provenance)
        self.assertIn("inspired_by", provenance)
        for fork in (
            "19Chris19/mcp-server-12306",
            "19Chris19/amap-lbs-skill",
            "19Chris19/flyai-skill",
            "19Chris19/universal-travel-planner-skill",
            "19Chris19/x-cli",
            "19Chris19/ego-lite",
        ):
            self.assertIn(fork, provenance)

    def test_required_publication_documents_exist(self):
        for name in (
            "README.md",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
            "SECURITY.md",
            "provenance.yml",
            "upstream-lock.yml",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_local_installer_uses_user_owned_tool_paths(self):
        script = (ROOT / "scripts" / "install-local.sh").read_text(encoding="utf-8")

        self.assertIn("python3 -m pipx", script)
        self.assertIn('npm install -g --prefix "$HOME/.local"', script)
        self.assertIn("@fly-ai/flyai-cli@1.0.16", script)
        self.assertIn("command -v uvx", script)
        self.assertIn("command -v ego-browser", script)
        self.assertIn("1.2.3", script)

    def test_ci_uses_live_github_actions_expressions(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertNotIn(r"\${{", workflow)
        self.assertIn("${{ matrix.python-version }}", workflow)
        self.assertIn("${{ secrets.GITHUB_TOKEN }}", workflow)
        self.assertIn("ruff check", workflow)
        self.assertIn("pip wheel", workflow)

    def test_python_distribution_includes_publication_notices(self):
        pyproject = (PLUGIN / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('license = "MIT"', pyproject)
        self.assertIn('license-files = ["LICENSE"]', pyproject)
        for name in ("LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"):
            self.assertTrue((PLUGIN / name).is_file(), name)
        self.assertEqual(
            (PLUGIN / "LICENSE").read_text(encoding="utf-8"),
            (ROOT / "LICENSE").read_text(encoding="utf-8"),
        )

    def test_mcp_launcher_exposes_only_provider_specific_credentials(self):
        launcher = PLUGIN / "scripts" / "run-with-credentials.sh"
        with tempfile.TemporaryDirectory() as directory:
            credentials = Path(directory) / "credentials.env"
            credentials.write_text(
                "AMAP_WEBSERVICE_KEY=amap-test\n"
                "FLYAI_API_KEY=fly-test\n"
                "VARIFLIGHT_API_KEY=vari-test\n",
                encoding="utf-8",
            )
            base_env = {
                "PATH": os.environ["PATH"],
                "XDG_CONFIG_HOME": directory,
            }
            xdg_credentials = Path(directory) / "china-travel-assistant" / "credentials.env"
            xdg_credentials.parent.mkdir(exist_ok=True)
            credentials.replace(xdg_credentials)
            rail = subprocess.run(
                [str(launcher), "12306", "env"],
                check=True,
                capture_output=True,
                text=True,
                env=base_env,
            )
            variflight = subprocess.run(
                [str(launcher), "variflight", "env"],
                check=True,
                capture_output=True,
                text=True,
                env=base_env,
            )
            environment_override = subprocess.run(
                [str(launcher), "variflight", "env"],
                check=True,
                capture_output=True,
                text=True,
                env={**base_env, "VARIFLIGHT_API_KEY": "env-test"},
            )

        for secret in ("amap-test", "fly-test", "vari-test"):
            self.assertNotIn(secret, rail.stdout)
        self.assertNotIn("amap-test", variflight.stdout)
        self.assertNotIn("fly-test", variflight.stdout)
        self.assertIn("VARIFLIGHT_API_KEY=vari-test", variflight.stdout)
        self.assertIn("VARIFLIGHT_API_KEY=env-test", environment_override.stdout)
        self.assertNotIn("VARIFLIGHT_API_KEY=vari-test", environment_override.stdout)


if __name__ == "__main__":
    unittest.main()
