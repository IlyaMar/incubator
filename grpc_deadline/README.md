# Build
go build -o bin/client ./client 
go build -o bin/server ./server

# Run
```
./bin/server -timeout 0s

./bin/client -delay 5s -deadline 20s \
-retry-max-attempts 30 -attempt-timeout 1000ms -service-config config/grpc_service_config.json \
-keepalive-time 1s -keepalive-timeout 100ms 

```

# Inject network black hole
```
sudo ./scripts/net-blackhole.sh on 50100
```