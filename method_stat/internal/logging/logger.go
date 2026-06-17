package logging

import (
	"io"
	"log/slog"
	"os"
	"path/filepath"
)

func New(logFile string, alsoStdout bool) (*slog.Logger, io.Closer, error) {
	if err := os.MkdirAll(filepath.Dir(logFile), 0o755); err != nil {
		return nil, nil, err
	}
	f, err := os.OpenFile(logFile, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return nil, nil, err
	}
	var w io.Writer = f
	if alsoStdout {
		w = io.MultiWriter(f, os.Stdout)
	}
	logger := slog.New(slog.NewJSONHandler(w, &slog.HandlerOptions{Level: slog.LevelInfo}))
	return logger, f, nil
}
