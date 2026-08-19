#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/china-travel-assistant"
target="$config_dir/credentials.env"

mkdir -p "$config_dir"
if [ ! -f "$target" ]; then
  cp "$root_dir/.env.example" "$target"
fi
chmod 600 "$target"
printf '%s\n' "$target"
