#!/bin/sh
set -eu

if [ "$#" -lt 2 ]; then
  echo "usage: run-with-credentials.sh PROVIDER COMMAND [ARG ...]" >&2
  exit 2
fi

provider=$1
shift
config_home="${XDG_CONFIG_HOME:-${HOME:?HOME is required}/.config}"
credentials_file="${CHINA_TRAVEL_CREDENTIALS_FILE:-$config_home/china-travel-assistant/credentials.env}"

read_credential() {
  awk -v wanted="$1" '
    {
      line = $0
      sub(/^[ \t]+/, "", line)
      sub(/^export[ \t]+/, "", line)
      separator = index(line, "=")
      if (!separator) next
      key = substr(line, 1, separator - 1)
      gsub(/[ \t]+/, "", key)
      if (key != wanted) next
      value = substr(line, separator + 1)
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      quote = substr(value, 1, 1)
      if ((quote == "\"" || quote == "\047") && substr(value, length(value), 1) == quote) {
        value = substr(value, 2, length(value) - 2)
      }
      print value
      exit
    }
  ' "$credentials_file"
}

case "$provider" in
  12306)
    unset AMAP_WEBSERVICE_KEY AMAP_JSAPI_KEY AMAP_SECURITY_CODE
    unset FLYAI_API_KEY VARIFLIGHT_API_KEY VIGOLIVE_API_KEY
    ;;
  variflight)
    unset AMAP_WEBSERVICE_KEY AMAP_JSAPI_KEY AMAP_SECURITY_CODE
    unset FLYAI_API_KEY VIGOLIVE_API_KEY
    if [ "${VARIFLIGHT_API_KEY+x}" != x ] && [ -f "$credentials_file" ]; then
      variflight_key=$(read_credential VARIFLIGHT_API_KEY)
      if [ -n "$variflight_key" ]; then
        export VARIFLIGHT_API_KEY=$variflight_key
      fi
    fi
    ;;
  *)
    echo "unsupported credential provider: $provider" >&2
    exit 2
    ;;
esac

exec "$@"
