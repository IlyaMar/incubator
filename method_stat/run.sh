#!/usr/bin/env zsh

set -euo pipefail

# for service in $(ls config/*.yaml | sed 's/^config\///; s/\.yaml$//'); do
#   [[ "$service" == "common" ]] && continue
#   ./bin/discover --config=./config/${service}.yaml --stdout
# done


UNIFIED="output/methods.csv"
{
  echo "service,method,rps,failrate,p90,p99,p999"
  for f in output/*_methods.csv; do
    cat "$f"
  done
} > "$UNIFIED"
echo "wrote $UNIFIED"
