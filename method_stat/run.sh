#!/usr/bin/env zsh

set -euo pipefail

for service in $(ls config/*.yaml | sed 's/^config\///; s/\.yaml$//'); do
  ./bin/discover --config=./config/${service}.yaml --stdout
done
