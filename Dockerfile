# Stage 1: Build the frontend
FROM oven/bun:1 AS frontend-builder

WORKDIR /app/frontend

# Catch build argument and expose it to Vite
ARG APP_VERSION=dev
ENV VITE_APP_VERSION=$APP_VERSION

# Copy package files
COPY frontend/package.json frontend/bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code
COPY frontend .

# Build the application
# Set NODE_ENV to production for the build process
# This ensures Bun loads .env.production if present, and tools behave in production mode
RUN NODE_ENV=production bun run build

# Stage 2: Setup the backend and serve
FROM python:3.14-slim AS backend-runner

WORKDIR /app

# Catch build argument and expose it to the backend
ARG APP_VERSION=dev
ENV RAPTR_VERSION=$APP_VERSION

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies
# --frozen ensures we use the exact versions from uv.lock
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Install openssl for certificate generation
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Copy backend source code
COPY backend/app ./app
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Copy built frontend assets from the previous stage
# We place them in a 'static' directory inside the app or a sibling directory
# Adjusting to copy to /app/static for easier serving
COPY --from=frontend-builder /app/frontend/dist /app/static

# Expose the port
EXPOSE 8000

# Run the application using the entrypoint script
CMD ["/app/entrypoint.sh"]
