#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
plugin_dir="$root_dir/plugins/china-travel-assistant"

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
"$root_dir/scripts/setup-credentials.sh"

codex plugin marketplace add "$root_dir"
codex plugin add china-travel-assistant@china-travel-assistant

echo "Installation complete. Restart Codex before using the MCP servers."
