import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "readme"
README = ROOT / "README.md"
CREDENTIALS = ROOT / "plugins" / "china-travel-assistant" / "references" / "credentials.md"


class ReadmeTests(unittest.TestCase):
    def test_approved_readme_assets_exist_and_fit_publication_limits(self):
        gif = ASSETS / "china-travel-assistant.gif"
        dark = ASSETS / "china-travel-assistant-dark.jpeg"
        light = ASSETS / "china-travel-assistant-light.jpeg"

        for asset in (gif, dark, light):
            self.assertTrue(asset.is_file(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)

        self.assertLess(gif.stat().st_size, 2 * 1024 * 1024)
        self.assertEqual(gif.read_bytes()[:6], b"GIF89a")
        width, height = struct.unpack("<HH", gif.read_bytes()[6:10])
        self.assertEqual((width, height), (640, 271))

    def test_readme_starts_with_gif_and_exposes_installation_path(self):
        text = README.read_text(encoding="utf-8")
        first_image = re.search(r"!\[[^]]*\]\(([^)]+)\)|<img[^>]+src=[\"']([^\"']+)", text)
        self.assertIsNotNone(first_image)
        image_target = first_image.group(1) or first_image.group(2)
        self.assertEqual(image_target, "./assets/readme/china-travel-assistant.gif")
        self.assertIn("git clone https://github.com/19Chris19/china-travel-assistant", text)
        self.assertIn("./scripts/install-local.sh", text)
        self.assertIn("使用 $plan-china-trip", text)

    def test_readme_contains_runtime_capabilities_and_source_relationships(self):
        text = README.read_text(encoding="utf-8")
        for name in (
            "$plan-china-trip",
            "$search-china-flights",
            "$search-china-trains",
            "$plan-china-transfers",
            "$search-china-hotels",
            "$verify-travel-web",
        ):
            self.assertIn(name, text)
        for relationship in ("forked_from", "integrates_with", "inspired_by"):
            self.assertIn(relationship, text)
        for variable in (
            "AMAP_WEBSERVICE_KEY",
            "AMAP_JSAPI_KEY",
            "AMAP_SECURITY_CODE",
            "FLYAI_API_KEY",
            "VARIFLIGHT_API_KEY",
            "VIGOLIVE_API_KEY",
        ):
            self.assertIn(variable, text)
        for safety_phrase in ("不执行实名", "不执行支付", "不输出真实 Key"):
            self.assertIn(safety_phrase, text)

    def test_credentials_document_links_official_application_and_local_setup(self):
        text = CREDENTIALS.read_text(encoding="utf-8")
        for url in (
            "https://lbs.amap.com/api/webservice/create-project-and-key",
            "https://lbs.amap.com/api/javascript-api-v2/prerequisites",
            "https://open.fly.ai/",
            "https://mcp.variflight.com/",
        ):
            self.assertIn(url, text)
        self.assertIn("~/.config/china-travel-assistant/credentials.env", text)
        self.assertIn("0600", text)
        self.assertIn("VIGOLIVE_API_KEY", text)
        self.assertNotRegex(text, r"sk-[A-Za-z0-9_-]{20,}")

    def test_readme_design_tool_is_credited_as_inspiration(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("https://github.com/oil-oil/beautify-github-readme", text)
        self.assertIn("beautify-github-readme", (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8"))
        self.assertIn("https://github.com/oil-oil/beautify-github-readme", (ROOT / "provenance.yml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
