package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"

	greetv1 "github.com/ilya-martynov/incubator/grpc_deadline/gen/greet/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/status"
)

func main() {
	defaultDelay := time.Second
	if v := os.Getenv("REQUEST_DELAY"); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			defaultDelay = d
		}
	}

	addr := flag.String("addr", "localhost:50051", "gRPC server address")
	delay := flag.Duration("delay", defaultDelay, "delay between requests")
	name := flag.String("name", "client", "name sent in SayHello request")
	deadline := flag.Duration("deadline", 0,
		"total deadline for one loop iteration including all retry attempts (0 disables)")
	attemptTimeout := flag.Duration("attempt-timeout", 0,
		"deadline for a single SayHello attempt; each retry gets a fresh timeout (0 disables)")
	keepaliveTime := flag.Duration("keepalive-time", 10*time.Second, "gRPC keepalive ping period (0 disables)")
	keepaliveTimeout := flag.Duration("keepalive-timeout", 3*time.Second, "gRPC keepalive ping ack timeout")
	keepalivePermitWithoutStream := flag.Bool("keepalive-permit-without-stream", true,
		"send keepalive pings when there are no active RPCs")
	retryMaxAttempts := flag.Int("retry-max-attempts", 3,
		"max SayHello attempts per loop iteration (retries on DeadlineExceeded)")
	serviceConfigPath := flag.String("service-config", "config/grpc_service_config.json",
		"path to gRPC service config JSON for built-in retries (empty disables)")
	flag.Parse()

	var localTCPPort atomic.Int32

	dialOpts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithContextDialer(func(ctx context.Context, address string) (net.Conn, error) {
			var d net.Dialer
			c, err := d.DialContext(ctx, "tcp", address)
			if err != nil {
				return nil, err
			}
			if tcp, ok := c.LocalAddr().(*net.TCPAddr); ok {
				localTCPPort.Store(int32(tcp.Port))
			}
			return c, nil
		}),
	}
	if *keepaliveTime > 0 {
		dialOpts = append(dialOpts, grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                *keepaliveTime,
			Timeout:             *keepaliveTimeout,
			PermitWithoutStream: *keepalivePermitWithoutStream,
		}))
	}
	maxAttempts := *retryMaxAttempts
	if maxAttempts < 1 {
		maxAttempts = 1
	}
	if maxAttempts > 1 || *attemptTimeout > 0 {
		dialOpts = append(dialOpts, grpc.WithUnaryInterceptor(retryConfig{
			MaxAttempts:       maxAttempts,
			PerAttemptTimeout: *attemptTimeout,
		}.unaryClientInterceptor()))
	}
	serviceConfigInfo := "disabled"
	if *serviceConfigPath != "" {
		svcCfg, err := loadServiceConfig(*serviceConfigPath)
		if err != nil {
			log.Fatalf("service config: %v", err)
		}
		dialOpts = append(dialOpts, svcCfg)
		serviceConfigInfo = *serviceConfigPath
	}

	conn, err := grpc.NewClient(*addr, dialOpts...)
	if err != nil {
		log.Fatalf("dial: %v", err)
	}
	defer conn.Close()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	conn.Connect()
	if err := waitForReady(ctx, conn); err != nil {
		log.Fatalf("connect: %v", err)
	}

	client := greetv1.NewGreetServiceClient(conn)

	keepaliveInfo := "disabled"
	if *keepaliveTime > 0 {
		keepaliveInfo = fmt.Sprintf("time=%s timeout=%s permit_without_stream=%v",
			*keepaliveTime, *keepaliveTimeout, *keepalivePermitWithoutStream)
	}
	deadlineRetryInfo := fmt.Sprintf("max_attempts=%d attempt_timeout=%s", *retryMaxAttempts, *attemptTimeout)
	if *retryMaxAttempts <= 1 && *attemptTimeout == 0 {
		deadlineRetryInfo = "disabled"
	}
	deadlineInfo := "disabled"
	if *deadline > 0 {
		deadlineInfo = deadline.String()
	}
	log.Printf("sending SayHello to %s every %s (local tcp port %d, keepalive %s, grpc retry %s, deadline retry %s, deadline %s, Ctrl+C to stop)",
		*addr, *delay, localTCPPort.Load(), keepaliveInfo, serviceConfigInfo, deadlineRetryInfo, deadlineInfo)

	for n := 1; ; n++ {
		if err := ctx.Err(); err != nil {
			return
		}

		log.Printf("#%d sending request (local tcp port %d)", n, localTCPPort.Load())
		start := time.Now()
		reqCtx := ctx
		reqCancel := func() {}
		if *deadline > 0 {
			reqCtx, reqCancel = context.WithTimeout(ctx, *deadline)
		}
		resp, err := client.SayHello(reqCtx, &greetv1.SayHelloRequest{Name: *name})
		reqCancel()
		elapsed := time.Since(start)

		if err != nil {
			log.Printf("#%d error after %s: %v (%s)", n, elapsed, err, status.Convert(err).Code())
		} else {
			log.Printf("#%d ok after %s: %s", n, elapsed, resp.GetMessage())
		}

		select {
		case <-ctx.Done():
			return
		case <-time.After(*delay):
		}
	}
}

func waitForReady(ctx context.Context, conn *grpc.ClientConn) error {
	for {
		switch conn.GetState() {
		case connectivity.Ready:
			return nil
		case connectivity.TransientFailure, connectivity.Shutdown:
			return fmt.Errorf("connection state: %s", conn.GetState())
		}
		if !conn.WaitForStateChange(ctx, conn.GetState()) {
			return ctx.Err()
		}
	}
}
