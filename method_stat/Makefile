.PHONY: build run tidy clean

BIN := bin/discover

build:
	mkdir -p bin
	go build -o $(BIN) ./cmd/discover

run: build
	$(BIN) $(ARGS)

tidy:
	go mod tidy

clean:
	rm -rf bin logs
