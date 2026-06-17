# method_stat

Discover and read metrics from Monium (Yandex Solomon).
https://solomon.yandex-team.ru/webjars/swagger-ui/index.html

## Build

    make build

## Discover metrics

Place a valid IAM token in `~/.iam_token`:
```
ycp --profile=prod iam create-token > ~/.iam_token
```

then run:
```
    ./bin/discover \
      --project=<project_id> \
      --cluster='prod-*' \
      --label sensor=grpc_duration \
      --log-file=./logs/discover.log \
      --stdout
```
Found metrics are written as one JSON line per metric to the log file.
