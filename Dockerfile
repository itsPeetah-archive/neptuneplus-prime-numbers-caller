# Stage 1: Build the Go binaries
FROM golang:1.24-alpine AS builder

WORKDIR /app

COPY go.mod .

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/bin/program ./pkg

FROM alpine:latest AS function
EXPOSE 8080
WORKDIR /app

ARG PRIME_NUMBERS_URI=""
ENV PRIME_NUMBERS_URI=$PRIME_NUMBERS_URI

COPY --from=builder /app/bin/program .
ENTRYPOINT ["./program"]