#!/bin/sh
set -eu

credentials_file="${CHINA_TRAVEL_CREDENTIALS_FILE:-$HOME/.config/china-travel-assistant/credentials.env}"

if [ -f "$credentials_file" ]; then
  set -a
  # This file is user-owned and must be mode 0600.
  . "$credentials_file"
  set +a
fi

exec "$@"
