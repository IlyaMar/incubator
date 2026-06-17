#!/usr/bin/env bash
# monium.sh — minimal Solomon/Monium REST caller
# Usage:
#   ./monium.sh GET  /projects/yc.iam.service-cloud/sensors/labels
#   ./monium.sh POST /projects/yc.iam.service-cloud/sensors/labels '{"selectors":"{cluster=\"cloud-prod-a\"}","names":["method"]}'
#   ./monium.sh GET  /projects/yc.iam.service-cloud/clusters
#   ./monium.sh GET  /projects

set -euo pipefail

BASE_URL="${MONIUM_BASE_URL:-https://solomon.cloud.yandex-team.ru/api/v2}"
TOKEN_FILE="${IAM_TOKEN_FILE:-$HOME/.iam_token}"

if [[ ! -r "$TOKEN_FILE" ]]; then
  echo "IAM token file not found: $TOKEN_FILE" >&2
  exit 1
fi
TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
if [[ -z "$TOKEN" ]]; then
  echo "IAM token at $TOKEN_FILE is empty" >&2
  exit 1
fi

method="${1:?usage: $0 METHOD PATH [JSON_BODY]}"
path="${2:?usage: $0 METHOD PATH [JSON_BODY]}"
body="${3:-}"

url="${BASE_URL%/}${path}"

args=(
  -sS
  -X "$method"
  -H "Authorization: Bearer $TOKEN"
  -H "Accept: application/json"
  -w '\n--- HTTP %{http_code} (%{time_total}s) ---\n'
)

if [[ -n "$body" ]]; then
  args+=( -H "Content-Type: application/json" --data "$body" )
fi

curl "${args[@]}" "$url"
