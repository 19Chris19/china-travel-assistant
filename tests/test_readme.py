import re
import struct
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "readme"
README = ROOT / "README.md"
CREDENTIALS = ROOT / "plugins" / "china-travel-assistant" / "references" / "credentials.md"
SVG_ASSETS = (
    "section-quickstart.svg",
    "section-routing.svg",
    "section-security.svg",
    "section-sources.svg",
    "skill-system-map.svg",
    "provider-workflow.svg",
    "credential-boundary.svg",
    "provenance-map.svg",
)


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
            "https://ai.variflight.com/",
        ):
            self.assertIn(url, text)
        self.assertNotIn("https://mcp.variflight.com/", text)
        self.assertIn("~/.config/china-travel-assistant/credentials.env", text)
        self.assertIn("0600", text)
        self.assertIn("VIGOLIVE_API_KEY", text)
        self.assertNotRegex(text, r"sk-[A-Za-z0-9_-]{20,}")

    def test_readme_design_tool_is_credited_as_inspiration(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("https://github.com/oil-oil/beautify-github-readme", text)
        self.assertIn("beautify-github-readme", (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8"))
        self.assertIn("https://github.com/oil-oil/beautify-github-readme", (ROOT / "provenance.yml").read_text(encoding="utf-8"))

    def test_copyable_urls_are_not_joined_to_chinese_punctuation(self):
        text = README.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"https://[^\s)`>]+[。；，]")

    def test_readme_embeds_theme_overview_and_complete_visual_sequence(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("<picture>", text)
        self.assertIn("china-travel-assistant-dark.jpeg", text)
        self.assertIn("china-travel-assistant-light.jpeg", text)
        for name in SVG_ASSETS:
            self.assertIn(f"./assets/readme/{name}", text)

        visual_targets = re.findall(
            r"(?:src|srcset)=[\"'](\./assets/readme/[^\"']+)[\"']|"
            r"!\[[^]]*\]\((\./assets/readme/[^)]+)\)",
            text,
        )
        flattened = [target for pair in visual_targets for target in pair if target]
        self.assertGreaterEqual(len(flattened), 11)

    def test_svg_assets_are_accessible_local_and_github_safe(self):
        forbidden_tags = {"script", "foreignObject"}
        for name in SVG_ASSETS:
            path = ASSETS / name
            self.assertTrue(path.is_file(), path)
            self.assertLess(path.stat().st_size, 100 * 1024, path)
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?:href|src)=[\"']https?://", path)
            self.assertNotRegex(text, r"sk-[A-Za-z0-9_-]{20,}")

            root = ET.fromstring(text)
            self.assertEqual(root.tag.rsplit("}", 1)[-1], "svg", path)
            self.assertTrue(root.attrib.get("viewBox", "").startswith("0 0 1200 "), path)
            child_tags = {child.tag.rsplit("}", 1)[-1] for child in root.iter()}
            self.assertIn("title", child_tags, path)
            self.assertIn("desc", child_tags, path)
            self.assertTrue(forbidden_tags.isdisjoint(child_tags), path)


if __name__ == "__main__":
    unittest.main()
