# Data Persistence & Backups

RAPTR stores all data in its configured database (PostgreSQL or SQLite). This page covers how data is persisted, how to back it up, and how to recover from failures.

## What Is Stored Where

| Data | Storage | Persistence |
|---|---|---|
| All application data (users, assessments, activities, templates, etc.) | Database | Use Docker volume `postgres_data` (PostgreSQL) or mounted volume (SQLite) |
| Uploaded file attachments (images, evidence) | Database (binary column) | Same as above |
| SSL certificates | Filesystem | Mounted volume `./certs` (only when `TLS_ENABLED=true`) |
| Configuration | `.env` file | Host filesystem |
| Auto-generated secrets (`SECRET_KEY`, `ADMIN_PASSWORD`) | `.env` file | Host filesystem |

??? info "No external file storage"
    RAPTR stores all uploaded files directly in the database as binary data. There is no separate file storage (S3, local disk) to back up.

## Docker Volumes

### PostgreSQL

The default `docker-compose.yml` uses a named Docker volume for PostgreSQL data:

```bash
# Inspect the volume
docker volume inspect raptr_postgres_data

# Volume location on the host (varies by OS)
docker volume inspect raptr_postgres_data --format '{{ .Mountpoint }}'
```

This volume survives container restarts and recreation.

### SQLite

When using SQLite (`DB_ENGINE=sqlite`), the database is a single file at the path configured by `SQLITE_DB_PATH` (default: `raptr.db`). Mount a volume to persist it:

```bash
docker run -d \
  -e DB_ENGINE=sqlite \
  -e SQLITE_DB_PATH=/data/raptr.db \
  -v raptr_data:/data \
  ghcr.io/compasssecurity/raptr:latest
```

!!! warning "Without a volume mount, SQLite data is lost when the container is removed."

### Certificates Volume (`./certs`)

A bind mount from the host filesystem. SSL certificates are stored here and persist across container restarts. Only relevant when `TLS_ENABLED=true` (the default).

## Backing Up the Database

### PostgreSQL

#### Backup with `pg_dump`

Use `pg_dump` with custom format (`-Fc`). 

```bash
docker exec <container_name> pg_dump -U postgres -Fc raptr > backup_$(date +%Y%m%d_%H%M%S).dump
```

#### Restore wit `pg_restore`

Rrestore with `pg_restore --clean --create`:

```bash
docker compose stop raptr
docker exec -i <container_name> pg_restore -U postgres --clean --create -d postgres < backup.dump
docker compose start raptr
```

#### Automated Backups

Set up a cron job for regular backups:

```bash
# Add to crontab (crontab -e)
# Daily backup at 2:00 AM, keep last 30 days
0 2 * * * docker exec -i <container_name> pg_dump -U postgres -Fc raptr > /backups/raptr_$(date +\%Y\%m\%d).dump && find /backups -name "raptr_*.dump" -mtime +30 -delete
```

### SQLite

SQLite backups are simple file copies. Stop the application first to avoid copying a database mid-transaction:

```bash
# Stop the container, copy the file, restart
docker stop raptr
cp /path/to/raptr_data/raptr.db backup_$(date +%Y%m%d_%H%M%S).db
docker start raptr
```

Alternatively, use SQLite's `.backup` command without stopping the container:

```bash
docker exec raptr sqlite3 /data/raptr.db ".backup /data/backup.db"
docker cp raptr:/data/backup.db ./backup_$(date +%Y%m%d_%H%M%S).db
```

To restore, replace the database file with your backup:

```bash
docker stop raptr
cp backup.db /path/to/raptr_data/raptr.db
docker start raptr
```

## Database Schema Management

RAPTR manages its database schema with migrations (Alembic) and applies them automatically on every startup:

- **New database**: all tables are created
- **Upgrade to a newer RAPTR version**: only the schema changes that are missing are applied, existing data is kept
- **No change**: nothing happens

The database records its schema version in the table `alembic_version`. No manual steps are needed when upgrading.

!!! warning "Back up before upgrading"
    Schema changes can't be undone automatically once data has been changed. Create a database backup (see [Backing Up the Database](#backing-up-the-database)) before starting a newer RAPTR version.

??? info "Databases created before migration support"
    Databases created by RAPTR versions without migration support (they have tables but no `alembic_version`) can't be upgraded. RAPTR refuses to start with the message *"The database was created by a RAPTR version without migration support…"*. Back up the data you need, then start RAPTR with an empty database; it will be set up again.

## What to Back Up

For a complete disaster recovery, back up these items:

| Item | Location | Method |
|---|---|---|
| Database | Docker volume (PostgreSQL) or file (SQLite) | `pg_dump` or file copy |
| Environment configuration | `.env` | File copy |
| SSL certificates | `./certs/` | File copy (only if `TLS_ENABLED=true`) |
| Docker Compose file | `docker-compose.yml` | File copy / version control |
