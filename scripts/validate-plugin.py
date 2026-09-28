"""Repository-owned, Python 3.10-compatible Plugin and Skill release gate."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "china-travel-assistant"
EXPECTED = {
    "plan-china-trip", "search-china-flights", "search-china-trains",
    "plan-china-transfers", "search-china-hotels", "verify-travel-web",
    "explore-china-routes", "present-china-trip",
}


def main() -> int:
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    if manifest["name"] != "china-travel-assistant" or market["plugins"][0]["name"] != manifest["name"]:
        raise ValueError("Plugin identity mismatch")
    if manifest["skills"] != "./skills/" or manifest["mcpServers"] != "./.mcp.json":
        raise ValueError("Plugin paths mismatch")
    if not (PLUGIN / ".mcp.json").is_file():
        raise ValueError("MCP configuration missing")
    pyproject = (PLUGIN / "pyproject.toml").read_text(encoding="utf-8")
    package_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    if not package_version or package_version.group(1) != manifest["version"]:
        raise ValueError("package and Plugin versions differ")
    directories = {item.name for item in (PLUGIN / "skills").iterdir() if item.is_dir()}
    if directories != EXPECTED:
        raise ValueError("expected eight published Skills")
    corpus = json.loads((PLUGIN / "evals" / "trigger-cases.json").read_text(encoding="utf-8"))
    if set(corpus["cases"]) != EXPECTED:
        raise ValueError("Skill trigger corpus does not match published Skills")
    for name in EXPECTED:
        file = PLUGIN / "skills" / name / "SKILL.md"
        content = file.read_text(encoding="utf-8")
        if not content.startswith("---\n") or content.count("---") < 2:
            raise ValueError(f"invalid frontmatter: {name}")
        header = content.split("---", 2)[1]
        if f"name: {name}\n" not in header or "description: " not in header:
            raise ValueError(f"invalid Skill identity: {name}")
        if "Use when" not in header or "Do not use" not in header:
            raise ValueError(f"missing trigger boundaries: {name}")
        if not (file.parent / "agents" / "openai.yaml").is_file():
            raise ValueError(f"missing Skill UI metadata: {name}")
        samples = corpus["cases"][name]
        if len(samples["positive"]) != 8 or len(samples["negative"]) != 8:
            raise ValueError(f"incomplete trigger evaluation corpus: {name}")
    print("Plugin structure, eight strict Skill descriptions, corpus, and versions: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
