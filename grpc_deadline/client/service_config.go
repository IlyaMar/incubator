package main

import (
	"encoding/json"
	"fmt"
	"os"

	"google.golang.org/grpc"
)

func loadServiceConfig(path string) (grpc.DialOption, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read service config %q: %w", path, err)
	}

	var raw json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("parse service config %q: %w", path, err)
	}

	return grpc.WithDefaultServiceConfig(string(data)), nil
}
