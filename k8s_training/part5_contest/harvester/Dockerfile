
# Final stage
# FROM --platform=linux/amd64 python:3.8-slim
FROM --platform=linux/amd64 cr.yandex/crpsh8lqvs5nupoi3v85/iam-jammy-python:3

# Create a non-root user with explicit numeric ID
RUN addgroup --system -gid 1000 appgroup && adduser --system -uid 1000 -gid 1000 appuser

# Use the non-root user with numeric ID
USER 1000:1000


# Command to run the application
# CMD ["./resource-silo"]