# method_stat

CLI that pulls per-gRPC-method latency and request-rate statistics from
Monium / Yandex Solomon and writes them to a CSV.

## What it does

For a given Solomon project + cluster + service:

1. Discover the set of `method` label values by calling
   `POST /api/v2/projects/{projectId}/sensors/labels` with selectors built
   from `method_duration_labels`.
2. For each discovered method, run two SeL queries against
   `POST /api/v2/projects/{projectId}/sensors/data`:
   - `series_sum({...method_failrate_labels, method="<m>"})` → averaged over
     the time window to produce the `rps` column.
   - `histogram_percentile(p, integral({...method_duration_labels, method="<m>"}))`
     for `p ∈ {50, 90, 99}` → last value of the series produces `p50`/`p90`/`p99`.
3. Write `output/<service>_methods.csv` with columns
   `service, method, rps, p50, p90, p99` (no header).

## Layout

```
cmd/discover/main.go         CLI entry, config loading, CSV writer
internal/monium/client.go    HTTP client + IAM token loader
internal/monium/discover.go  /sensors/labels call + selector builder
internal/monium/data.go      /sensors/data call + LastValue + HistogramPercentileProgram
internal/monium/rps.go       RPSProgram + AverageValue
internal/monium/types.go     request/response DTOs
internal/logging/logger.go   slog JSON logger -> file (+ optional stdout)
config/common.yaml           shared bits (project, base_url, sensors, label names)
config/<service>.yaml        per-service overrides (cluster, service, app, ...)
output/<service>_methods.csv generated CSV
logs/discover.log            JSON log of every request and response
```

## Config

Two YAML files, deep-merged before parsing. Per-service overrides common;
nested maps merge recursively; lists are appended.

`config/common.yaml` typically contains: `base_url`, `project_id`,
`method_duration_labels.sensor`, `method_failrate_labels.sensor`,
`method_label_name`.

`config/<service>.yaml` typically contains: `cluster`, `service`,
`method_duration_labels.app` (and any per-service label overrides).

`cluster` and `service` are auto-injected into both
`method_duration_labels` and `method_failrate_labels` before the query is
built — don't duplicate them inside those maps.

Time window: `time_from` / `time_to` in config or `--from` / `--to` flags
(RFC3339). Default: `now - 1 month` → `now`.

## Auth

IAM token read from `~/.iam_token` (path overridable via `--token-file`),
sent as `Authorization: Bearer <token>`.

## Run

```
make build
./bin/discover --config=./config/<service>.yaml --stdout
```

`common.yaml` in the same directory as `--config` is auto-discovered;
override with `--common-config`. `--stdout` mirrors the JSON log to the
terminal; `--debug` adds raw response bodies to log records.

## Conventions worth knowing

- Solomon's `/sensors/data` responses come in two shapes —
  `{"timeseries": {...}}` for single-series results and
  `{"vector": [{"timeseries": {...}}]}` for vector results.
  `internal/monium/data.go:extractValues` handles both; new parsers
  should reuse it.
- Selector strings use double-quoted values
  (`{key="value", ...}`) and intentionally exclude the `project` label
  (it goes in the URL path).
- NaN / null / non-finite values are skipped by `AverageValue` and
  rendered as empty cells by the CSV writer.
- Adding a new metric kind: put the program builder and any
  response-shape-specific parsing in its own file under `internal/monium/`
  (see `rps.go` as the template), then wire it in `cmd/discover/main.go`.
