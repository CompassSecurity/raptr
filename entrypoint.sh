#!/bin/sh

# TLS_ENABLED (default: true) — set to "false" to serve plain HTTP
TLS_ENABLED="${TLS_ENABLED:-true}"

if [ "$TLS_ENABLED" = "true" ]; then
    # Generate self-signed certificate if it doesn't exist
    if [ ! -f /app/certs/key.pem ] || [ ! -f /app/certs/cert.pem ]; then
        echo "Generating self-signed certificate..."
        mkdir -p /app/certs
        openssl req -x509 -newkey rsa:4096 \
            -keyout /app/certs/key.pem \
            -out /app/certs/cert.pem \
            -sha256 -days 365 -nodes \
            -subj "/CN=localhost"
    fi

    echo "Starting with TLS enabled..."
    exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile /app/certs/key.pem --ssl-certfile /app/certs/cert.pem
else
    echo "Starting without TLS..."
    exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
