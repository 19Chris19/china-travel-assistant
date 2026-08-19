#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
plugin_dir="$root_dir/plugins/china-travel-assistant"
PATH="$HOME/.local/bin:$PATH"
export PATH

command -v codex >/dev/null 2>&1 || {
  echo "codex is required" >&2
  exit 2
}
command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required" >&2
  exit 2
}
command -v npm >/dev/null 2>&1 || {
  echo "npm is required" >&2
  exit 2
}
command -v uvx >/dev/null 2>&1 || {
  echo "uvx is required" >&2
  exit 2
}
command -v ego-browser >/dev/null 2>&1 || {
  echo "ego-browser is required" >&2
  exit 2
}

ego_skill_file=""
for candidate in "$HOME/.agents/skills/ego-browser/SKILL.md" "$HOME/.codex/skills/ego-browser/SKILL.md"; do
  if [ -f "$candidate" ]; then
    ego_skill_file=$candidate
    break
  fi
done
if [ -z "$ego_skill_file" ]; then
  echo "Ego Browser Skill 1.2.3 or newer is required" >&2
  exit 2
fi
python3 - "$ego_skill_file" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r'^\s*version:\s*["\']?([^"\'\s]+)', text, re.MULTILINE)
try:
    installed = tuple(int(part) for part in match.group(1).split("."))
except (AttributeError, ValueError):
    raise SystemExit("unable to read Ego Browser Skill version")
if installed < (1, 2, 3):
    raise SystemExit("Ego Browser Skill 1.2.3 or newer is required")
PY

if command -v pipx >/dev/null 2>&1; then
  pipx install --force "$plugin_dir"
elif python3 -m pipx --version >/dev/null 2>&1; then
  python3 -m pipx install --force "$plugin_dir"
else
  echo "pipx is required (install it with: python3 -m pip install --user pipx)" >&2
  exit 2
fi

flyai_version=""
if command -v flyai >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
  flyai_version=$(node -e '
    const fs = require("fs");
    const path = require("path");
    try {
      const entry = fs.realpathSync(process.argv[1]);
      const pkg = require(path.join(path.dirname(path.dirname(entry)), "package.json"));
      process.stdout.write(pkg.version || "");
    } catch (_) {}
  ' "$(command -v flyai)")
fi
if [ "$flyai_version" != "1.0.16" ]; then
  npm install -g --prefix "$HOME/.local" @fly-ai/flyai-cli@1.0.16
fi
command -v flyai >/dev/null 2>&1 || {
  echo "flyai was installed but $HOME/.local/bin is not usable" >&2
  exit 2
}
"$root_dir/scripts/setup-credentials.sh"

codex plugin marketplace add "$root_dir"
codex plugin add china-travel-assistant@china-travel-assistant

echo "Installation complete. Restart Codex before using the MCP servers."
