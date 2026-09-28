#!/bin/sh
set -eu

provider=${1:-amap}
case "$provider" in amap|flyai|variflight) ;; *) echo "Choose amap, flyai or variflight" >&2; exit 2 ;; esac
root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
data_home="${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}"
ui_root="$data_home/china-travel-assistant/credential-ui"

command -v node >/dev/null 2>&1 || { echo "Node 22.18+ is required for the credential page" >&2; exit 2; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||a===22&&b>=18?0:2)' || {
  echo "Node 22.18+ is required for the credential page" >&2
  exit 2
}
command -v npm >/dev/null 2>&1 || { echo "npm is required for the optional credential page" >&2; exit 2; }
if [ ! -f "$ui_root/src/profile.ts" ]; then
  mkdir -p "$(dirname "$ui_root")"
  cp -R "$root_dir/plugins/china-travel-assistant/credential-ui" "$ui_root"
fi
if [ ! -d "$ui_root/node_modules/@napi-rs/keyring" ]; then
  (cd "$ui_root" && npm ci --ignore-scripts --no-audit --no-fund)
fi
exec node "$ui_root/src/profile.ts" setup "$provider"
