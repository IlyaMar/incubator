.PHONY: proto build run run-client blackhole-on blackhole-off blackhole-status

# Default gRPC port; override: make blackhole-on PORTS="50051 8080"
PORTS ?= 50051
BLACKHOLE_LOOPBACK ?=
BLACKHOLE_OPTS := $(if $(BLACKHOLE_LOOPBACK),--loopback,)

proto:
	protoc \
		--go_out=. --go_opt=module=github.com/ilya-martynov/incubator/grpc_deadline \
		--go-grpc_out=. --go-grpc_opt=module=github.com/ilya-martynov/incubator/grpc_deadline \
		api/greet.proto

build: proto
	go build -o bin/server ./server
	go build -o bin/client ./client

run: build
	./bin/server

run-client: build
	./bin/client

# Silent TCP blackhole via macOS pf (requires sudo).
blackhole-on:
	sudo ./scripts/net-blackhole.sh on $(BLACKHOLE_OPTS) $(PORTS)

blackhole-off:
	sudo ./scripts/net-blackhole.sh off

blackhole-status:
	sudo ./scripts/net-blackhole.sh status


#  go build -o bin/client ./client 