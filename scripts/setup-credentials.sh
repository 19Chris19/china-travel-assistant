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
source_ui="$root_dir/plugins/china-travel-assistant/credential-ui"
mkdir -p "$ui_root/manifests" "$ui_root/src" "$ui_root/public"
cp "$source_ui/package.json" "$source_ui/package-lock.json" "$ui_root/"
cp "$source_ui/manifests/"*.json "$ui_root/manifests/"
cp "$source_ui/src/"*.ts "$ui_root/src/"
cp "$source_ui/public/"* "$ui_root/public/"
(cd "$ui_root" && npm ci --ignore-scripts --no-audit --no-fund)
exec node "$ui_root/src/profile.ts" setup "$provider"
