#!/bin/sh
set -eu

if [ "$#" -lt 2 ]; then
  echo "usage: run-with-credentials.sh PROVIDER COMMAND [ARG ...]" >&2
  exit 2
fi
provider=$1
shift
case "$provider" in
  12306|variflight) ;;
  *) echo "unsupported credential provider: $provider" >&2; exit 2 ;;
esac

unset AMAP_WEBSERVICE_KEY AMAP_JSAPI_KEY AMAP_SECURITY_CODE
unset FLYAI_API_KEY VIGOLIVE_API_KEY
unset QWEATHER_API_HOST QWEATHER_KEY_ID QWEATHER_DEVELOPER_ID QWEATHER_PROJECT_ID QWEATHER_PRIVATE_KEY_PATH
if [ "$provider" = 12306 ]; then
  unset VARIFLIGHT_API_KEY
  exec "$@"
fi
if [ -n "${VARIFLIGHT_API_KEY:-}" ]; then
  exec "$@"
fi
data_home="${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}"
ui_root="${CHINA_TRAVEL_CREDENTIAL_UI:-$data_home/china-travel-assistant/credential-ui}"
if ! command -v node >/dev/null 2>&1 || [ ! -f "$ui_root/src/profile.ts" ]; then
  echo "Variflight profile unavailable; run scripts/setup-credentials.sh variflight" >&2
  exit 2
fi
exec node "$ui_root/src/profile.ts" run variflight -- "$@"
