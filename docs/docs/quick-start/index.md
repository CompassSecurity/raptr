# Quick Start

Get up and running with RAPTR in minutes — try the online sandbox or run it locally with a single command.

---

## Online Sandbox

The fastest way to explore RAPTR is our public sandbox instance. No setup required.

[Open Sandbox :material-open-in-new:](https://sandbox.raptr.app){ .md-button .md-button--primary  target="_blank"}

??? info "Credentials"

    ```
    Username: admin@raptr.app
    Password: Password.123
    ```

!!! warning "Daily reset"
    The sandbox database is reset every day at **00:00 UTC** (midnight). Any data you create will be deleted. The sandbox is intended for exploration only.

---

## Run Locally

Run RAPTR as a single container using SQLite — no database setup needed:

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
  ghcr.io/CompassSecurity/raptr:latest
```

Open [http://localhost:8000](http://localhost:8000) and log in with the credentials above.

??? tip "What this does"
    - Starts RAPTR on port **8000** with plain HTTP (no TLS)
    - Uses **SQLite** as the database, stored in the `raptr_data` Docker volume
    - Creates a default admin account with the email and password you specified

!!! note "For production use"
    The SQLite setup is great for trying out RAPTR, but is not recommended for production. For a persistent deployment with PostgreSQL, TLS, and reverse proxy configuration, see the [Deployment Guide](../admin-guide/deployment.md).
