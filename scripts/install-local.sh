#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
plugin_dir="$root_dir/plugins/china-travel-assistant"
PATH="$HOME/.local/bin:$PATH"
export PATH

command -v codex >/dev/null 2>&1 || { echo "Codex CLI is required" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.10+ is required" >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 2)' || {
  echo "Python 3.10+ is required" >&2
  exit 2
}
if command -v pipx >/dev/null 2>&1; then
  pipx install --force "$plugin_dir"
elif python3 -m pipx --version >/dev/null 2>&1; then
  python3 -m pipx install --force "$plugin_dir"
else
  echo "pipx is required; install it with a Python 3.10+ environment" >&2
  exit 2
fi

codex plugin marketplace add "$root_dir"
codex plugin add china-travel-assistant@china-travel-assistant
echo "Core installed. Optional providers: scripts/install-optional.sh --help"
echo "Restart Codex to reload the plugin. Run travel-assistant doctor for status."
