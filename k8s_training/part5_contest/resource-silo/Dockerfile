# Build stage
FROM --platform=linux/amd64 golang:1.21 AS builder

# Set working directory
WORKDIR /app

# Copy Go module files
COPY main.go .
COPY go.mod ./

# Build the application with static linking
RUN CGO_ENABLED=0 go build -a -installsuffix cgo -o resource-silo .

# Final stage
FROM --platform=linux/amd64 alpine:3.18

# Add CA certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create a non-root user with explicit numeric ID
RUN addgroup -S -g 1000 appgroup && adduser -S -u 1000 -g 1000 appuser -G appgroup

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/resource-silo .

# Use the non-root user with numeric ID
USER 1000:1000

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["./resource-silo"]