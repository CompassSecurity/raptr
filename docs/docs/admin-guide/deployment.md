# Deployment

This page covers how to deploy and run RAPTR in different environments.

## Available Container Images

For your convenience, we provide the following RAPTR container images:

- `ghcr.io/compasssecurity/raptr:latest` - The image is updated whenever a merge to the main branch is performed.
- `ghcr.io/compasssecurity/raptr:v{version}` - A dedicated versioned image is created from time to time. This is maintained through Git tags. An entry in the [Release Notes](../release-notes/index.md) for the version will be available.

```bash
docker pull ghcr.io/compasssecurity/raptr:latest
```

The RAPTR container image combines the backend and frontend into a single container. The frontend is served by the backend using FastAPI's StaticFiles.

??? tip "Build your own Images"
    If you prefere to have dedicated containers for the frontend and backend you can build your own images See [Developer Guide](../developer-guide/index.md)

## Docker Compose (Recommended)

The recommended way to run RAPTR is via Docker Compose. The provided `docker-compose.yml` starts two services:

- **db** — PostgreSQL 15 database
- **raptr** — RAPTR application (frontend + backend)

### Prerequisites

- Docker or Podman and Docker Compose or Podman Compose
- A `.env` file with your configuration (see [Configuration](configuration.md))
- The `docker-compose.yml` file from [Github](https://github.com/CompassSecurity/raptr/blob/main/docker-compose.yml)

### Quick Start

1. Get the docker-compose file from [Github](https://github.com/CompassSecurity/raptr/blob/main/docker-compose.yml)

2. Create a `.env` file:

    ```env
        # Application
        APPLICATION_NAME=RAPTR-YourOrg
        LOG_LEVEL=INFO
        FASTAPI_DOCUMENTATION=false
        CORS_ENABLED=false

        # Admin account
        ADMIN_EMAIL=admin@your-org.something

        # Database
        DB_ENGINE=postgres
        POSTGRES_USER=raptr-db-user
        POSTGRES_PASSWORD=a-very-strong-password-here
        POSTGRES_DB=raptr
        POSTGRES_HOST=db
        POSTGRES_PORT=5432

        # Security
        MIN_PASSWORD_LENGTH=12

        # External data sources
        CUSTOM_DATA_URL=https://api.github.com/repos/your-org/raptr-templates/zipball/main
        CUSTOM_DATA_TOKEN=ghp_your_github_pat_here
    ```

    ??? bug "Provided `docker-compose.yml` is not optimal"
        The provided `docker-compose.yml` is not optimal:

        - If you choose to disable TLS ` TLS_ENABLED=false`, the RAPTR container will still mount the `certs` volume. This is not necessary and can be removed.
        - The `db` service uses the same `.env` file as the `raptr` service. This makes many environment variables, such as the JWT secret key and the default admin password, accessible to the database container. If this concerns you, choose dedicated `.env` files.

3. Start the services:

    ```bash
    docker compose up -d
    ```

4. Open RAPTR at `https://localhost:8000`

    ??? warning "Self-signed certificate"
        If you did not disable TLS `TLS_ENABLED=false`, the first launch generates a self-signed SSL certificate if you did not provide your own through the `certs` volume. Your browser will show a security warning — this is expected.

5. Log in with the admin account. On first launch, `SECRET_KEY` and `ADMIN_PASSWORD` are auto-generated and written to `.env`. Check the file for your credentials.

    ??? tip "Set your own default password"
        If you want to set a default password for the default administrator set the `ADMIN_PASSWORD` environment variable in your `.env` file.


## Single Container with SQLite

You can run RAPTR as a single container without PostgreSQL by using SQLite. This is useful for quick demos, testing, or small deployments.

```bash
docker run -d \
  --name raptr \
  -p 8000:8000 \
  -e DB_ENGINE=sqlite \
  -e SQLITE_DB_PATH=/data/raptr.db \
  -e TLS_ENABLED=false \
  -e ADMIN_EMAIL=admin@raptr.app \
  -e ADMIN_PASSWORD=your-secure-password \
  -v raptr_data:/data \
  ghcr.io/compasssecurity/raptr:latest
```

This starts RAPTR on `http://localhost:8000` with:

- **SQLite** as the database (stored in the `raptr_data` volume)
- **No TLS** (plain HTTP) — add your own certs or omit `TLS_ENABLED` for self-signed HTTPS
- **Default Admin** a default admin account is created with the email `admin@raptr.app`
- **Default Admin Password** the default admin password is set to `your-secure-password`

For more configuration options, use `--env-file`:

```bash
docker run -d \
  --name raptr \
  -p 8000:8000 \
  --env-file .env \
  -v raptr_data:/data \
  ghcr.io/compasssecurity/raptr:latest
```

??? tip "Persisting data"
    The `-v raptr_data:/data` volume ensures your SQLite database survives container restarts. Without it, all data is lost when the container is removed.

??? warning "SQLite limitations"
    SQLite is not recommended for production use.

## Exposing RAPTR with a Reverse Proxy

Here is an example docker-compose.yml file that exposes RAPTR with the caddy reverse proxy:

```yaml
services:
  db:
    image: postgres:15-alpine
    restart: always
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  raptr:
    image: ghcr.io/CompassSecurity/raptr:latest
    restart: always
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  caddy:
    image: caddy:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - raptr

volumes:
  postgres_data:
  caddy_data:
  caddy_config:
```

The Caddyfile should look like this:

```
raptr.your-org.something {
    reverse_proxy raptr:8000
}
```

## TLS/HTTPS Certificates

By default, RAPTR container images generate a self-signed certificate on first start:

- **Key**: `/app/certs/key.pem` (RSA 4096-bit)
- **Certificate**: `/app/certs/cert.pem` (365-day validity, CN=localhost)

You can disable TLS through the `TLS_ENABLED=false` environment variable.

### Using Production Certificates

To use proper certificates in your container, mount them into the container:

1. Place your certificate and key files in a `certs/` directory:

    ```
    certs/
    ├── cert.pem    # Your SSL certificate (or fullchain)
    └── key.pem     # Your private key
    ```

2. The Docker Compose volume mount `./certs:/app/certs` will pick them up automatically

## Building from Source

To build the Docker image locally:

```bash
git clone https://github.com/CompassSecurity/raptr.git
cd raptr
docker build -t raptr .
```

The Dockerfile uses a multi-stage build:

1. **Stage 1** — Builds the Vue 3 frontend using Bun
2. **Stage 2** — Sets up the Python 3.14 backend with `uv`, copies the built frontend assets into `/app/static`

To use your local build in Docker Compose, replace the `image` field:

```yaml
raptr:
  build: .
  # image: ghcr.io/compasssecurity/raptr:latest  # comment out
```

## Running Locally (Development)

For development without Docker:

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- [Bun](https://bun.sh/) (for the frontend)
- PostgreSQL 15+ running locally

### Backend

```bash
cd backend
uv sync
uv run fastapi dev
```

The backend starts at `http://localhost:8000` with hot-reload enabled.

??? tip "CORS"
    You need to enable CORS for this setup. Add `CORS_ENABLED=true` to your `.env` file. The default CORS settings should allow origins from `http://localhost:5173` and `http://127.0.0.1:5173`.
    

### Frontend

```bash
cd frontend
bun install
bun dev
```

The frontend dev server starts at `http://localhost:5173` and proxies API requests to the backend.

### Documentation

```
cd backend
uv run zensical serve --config-file ../docs/zensical.toml -a 127.0.0.1:8001
```

The documentation server starts at `http://localhost:8001`.

## First Launch

On the very first start, RAPTR performs the following initialization:

1. **SECRET_KEY** — If not set in `.env`, a secure 64-character hex key is generated and appended to `.env`. This key signs JWT tokens
2. **ADMIN_PASSWORD** — If not set in `.env`, a secure 32-character password is generated and appended to `.env`
3. **Database tables** — All tables are created if they don't exist (no migration of tables)
4. **Admin user** — Created with the email from `ADMIN_EMAIL` and the generated password
