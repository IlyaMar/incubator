package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type retryConfig struct {
	MaxAttempts       int
	PerAttemptTimeout time.Duration
}

func (c retryConfig) unaryClientInterceptor() grpc.UnaryClientInterceptor {
	maxAttempts := c.MaxAttempts
	if maxAttempts < 1 {
		maxAttempts = 1
	}

	return func(
		ctx context.Context,
		method string,
		req, reply any,
		cc *grpc.ClientConn,
		invoker grpc.UnaryInvoker,
		opts ...grpc.CallOption,
	) error {
		var lastErr error
		for attempt := 1; attempt <= maxAttempts; attempt++ {
			attemptCtx := ctx
			cancel := func() {}
			if c.PerAttemptTimeout > 0 {
				attemptCtx, cancel = context.WithTimeout(ctx, c.PerAttemptTimeout)
			}

			lastErr = invoker(attemptCtx, method, req, reply, cc, opts...)
			cancel()

			if lastErr == nil {
				return nil
			}
			if status.Code(lastErr) != codes.DeadlineExceeded || attempt == maxAttempts {
				return lastErr
			}

			log.Printf("retry after deadline exceeded (attempt %d/%d): %v",
				attempt, maxAttempts, lastErr)
		}
		return lastErr
	}
}
