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
	deadline := flag.Duration("deadline", 0, "per-request deadline (0 disables)")
	flag.Parse()

	var localTCPPort atomic.Int32

	conn, err := grpc.NewClient(*addr,
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
	)
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

	log.Printf("sending SayHello to %s every %s (local tcp port %d, Ctrl+C to stop)",
		*addr, *delay, localTCPPort.Load())

	for n := 1; ; n++ {
		if err := ctx.Err(); err != nil {
			return
		}

		reqCtx := ctx
		cancel := func() {}
		if *deadline > 0 {
			reqCtx, cancel = context.WithTimeout(ctx, *deadline)
		}

		log.Printf("#%d sending request (local tcp port %d)", n, localTCPPort.Load())
		start := time.Now()
		resp, err := client.SayHello(reqCtx, &greetv1.SayHelloRequest{Name: *name})
		cancel()
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
