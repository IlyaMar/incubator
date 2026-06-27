#!/usr/bin/env bash
# monium_query.sh — POST a Monium /sensors/data query, reading the SeL
# program text from stdin. Time window defaults to [now - 1h, now] UTC.
# Prints the JSON response to stdout.
#
# Usage:
#   ./scripts/monium_query.sh < program.sel
#   echo 'series_sum({cluster="prod-iam-access-service", method="grpc.health.v1.Health/Check"})' \
#     | ./scripts/monium_query.sh
#
# Environment overrides:
#   MONIUM_BASE_URL  — defaults to https://solomon.cloud.yandex-team.ru/api/v2
#   MONIUM_PROJECT   — defaults to project_id from config/common.yaml
#   MONIUM_CONFIG    — path to common config (defaults to ../config/common.yaml)
#   IAM_TOKEN_FILE   — defaults to ~/.iam_token

set -euo pipefail

if [[ -t 0 ]]; then
  echo "usage: $0 < program.sel  (pipe SeL program text on stdin)" >&2
  exit 2
fi
program="$(cat)"
if [[ -z "${program//[[:space:]]/}" ]]; then
  echo "empty program on stdin" >&2
  exit 2
fi

read -r FROM_TS TO_TS < <(python3 -c '
from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc).replace(microsecond=0)
print((now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ"))
')

body=$(PROGRAM="$program" FROM="$FROM_TS" TO="$TO_TS" python3 -c '
import json, os
print(json.dumps({"program": os.environ["PROGRAM"], "from": os.environ["FROM"], "to": os.environ["TO"]}))
')

BASE_URL="${MONIUM_BASE_URL:-https://solomon.cloud.yandex-team.ru/api/v2}"
TOKEN_FILE="${IAM_TOKEN_FILE:-$HOME/.iam_token}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${MONIUM_CONFIG:-$SCRIPT_DIR/../config/common.yaml}"

if [[ -n "${MONIUM_PROJECT:-}" ]]; then
  PROJECT="$MONIUM_PROJECT"
elif [[ -r "$CONFIG" ]]; then
  PROJECT="$(grep -E '^project_id:' "$CONFIG" | head -1 | sed -E 's/^project_id: *//; s/^"//; s/"$//')"
fi

if [[ -z "${PROJECT:-}" ]]; then
  echo "project_id not set (use MONIUM_PROJECT or set project_id in $CONFIG)" >&2
  exit 1
fi

if [[ ! -r "$TOKEN_FILE" ]]; then
  echo "IAM token file not found: $TOKEN_FILE" >&2
  exit 1
fi
TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
if [[ -z "$TOKEN" ]]; then
  echo "IAM token at $TOKEN_FILE is empty" >&2
  exit 1
fi

url="${BASE_URL%/}/projects/$PROJECT/sensors/data"

curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  --data "$body" \
  "$url"
