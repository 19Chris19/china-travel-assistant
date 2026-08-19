import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "china-travel-assistant"


class SecurityTests(unittest.TestCase):
    def test_runtime_and_skills_have_no_forbidden_browser_dependencies(self):
        roots = [
            PLUGIN_ROOT / "src",
            PLUGIN_ROOT / "skills",
            PLUGIN_ROOT / "scripts",
            PLUGIN_ROOT / ".mcp.json",
            PLUGIN_ROOT / "pyproject.toml",
        ]
        forbidden = ("kimi-webbridge", "kimi webbridge", "kimi_webbridge", "10086", "playwright")
        for root in roots:
            paths = [root] if root.is_file() else root.rglob("*")
            for path in paths:
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                for token in forbidden:
                    self.assertNotIn(token, text, f"{token} found in {path}")

    def test_repository_has_no_embedded_secret_values(self):
        secret_patterns = (
            re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            re.compile(
                r"(?i)(?:AMAP_[A-Z0-9_]*|VARIFLIGHT_API_KEY|FLYAI_API_KEY|VIGOLIVE_API_KEY)"
                r"[ \t]*[=:][ \t]*['\"]?[A-Za-z0-9_-]{16,}"
            ),
        )
        ignored = {".git"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in ignored for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in secret_patterns:
                self.assertIsNone(pattern.search(text), f"secret-like value found in {path}")


if __name__ == "__main__":
    unittest.main()
