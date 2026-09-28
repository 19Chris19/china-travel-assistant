#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
usage() { echo "Usage: $0 --12306|--flyai|--variflight|--ego|--credentials [amap|flyai|variflight]"; }
case "${1:---help}" in
  --12306)
    command -v uvx >/dev/null 2>&1 || { echo "uvx is needed for 12306 MCP" >&2; exit 2; }
    echo "12306 MCP is ready to launch through the plugin."
    ;;
  --flyai)
    command -v npm >/dev/null 2>&1 || { echo "npm is needed for FlyAI CLI" >&2; exit 2; }
    npm install -g --prefix "$HOME/.local" @fly-ai/flyai-cli@1.0.16
    ;;
  --variflight)
    command -v npm >/dev/null 2>&1 || { echo "npm is needed for Variflight MCP" >&2; exit 2; }
    npm install -g --prefix "$HOME/.local" @variflight-ai/variflight-mcp@1.0.3
    ;;
  --ego)
    command -v ego-browser >/dev/null 2>&1 || { echo "Install Ego Browser Skill and CLI 1.2.3+ separately" >&2; exit 2; }
    echo "Ego Browser CLI found; verify Skill version with travel-assistant doctor."
    ;;
  --credentials) shift; exec "$root_dir/scripts/setup-credentials.sh" "${1:-amap}" ;;
  --help) usage ;;
  *) usage >&2; exit 2 ;;
esac
