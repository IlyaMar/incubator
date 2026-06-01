package main

import (
	"context"
	"flag"
	"log"
	"net"
	"os"
	"time"

	greetv1 "github.com/ilya-martynov/incubator/grpc_deadline/gen/greet/v1"
	"google.golang.org/grpc"
)

type greetServer struct {
	greetv1.UnimplementedGreetServiceServer
	responseDelay time.Duration
}

func (s *greetServer) SayHello(ctx context.Context, req *greetv1.SayHelloRequest) (*greetv1.SayHelloResponse, error) {
	select {
	case <-time.After(s.responseDelay):
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	name := req.GetName()
	if name == "" {
		name = "world"
	}

	return &greetv1.SayHelloResponse{Message: "Hello, " + name}, nil
}

func main() {
	defaultTimeout := 2 * time.Second
	if v := os.Getenv("RESPONSE_TIMEOUT"); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			defaultTimeout = d
		}
	}

	timeout := flag.Duration("timeout", defaultTimeout, "delay before sending a response")
	addr := flag.String("addr", ":50051", "gRPC listen address")
	flag.Parse()

	lis, err := net.Listen("tcp", *addr)
	if err != nil {
		log.Fatalf("listen: %v", err)
	}

	srv := grpc.NewServer()
	greetv1.RegisterGreetServiceServer(srv, &greetServer{responseDelay: *timeout})

	log.Printf("gRPC server listening on %s (response delay: %s)", *addr, *timeout)
	if err := srv.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
