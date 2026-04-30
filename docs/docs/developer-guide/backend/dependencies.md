# Dependencies

All dependencies are managed via [uv](https://docs.astral.sh/uv/) and defined in `pyproject.toml`.

## Runtime Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi[standard]` | Web framework — includes Uvicorn, Starlette, and standard extras (CORS, form parsing, etc.) |
| `sqlalchemy` | ORM — database models, queries, and relationships using SQLAlchemy 2.0+ `Mapped` types |
| `pydantic-settings` | Configuration management — loads settings from environment variables with type validation |
| `psycopg` / `psycopg-binary` | PostgreSQL adapter — async-capable driver for production database connections |
| `pyjwt[crypto]` | JWT handling — token creation, validation, and cryptographic signing (RS256/HS256) |
| `pyotp` | TOTP/MFA — generates and validates time-based one-time passwords for multi-factor authentication |
| `pwdlib[argon2]` | Password hashing — secure password storage using the Argon2 algorithm |
| `jinja2` | Templating — used by FastAPI for HTML responses and by report generation |
| `docxtpl` | DOCX report generation — renders Word documents from Jinja2-based templates |
| `markdown-it-py` | Markdown rendering — converts markdown content to HTML for DOCX report fields |
| `pyyaml` | YAML parsing — used for reading structured data files (MITRE ATT&CK, custom seed data) |
| `pathvalidate` | Path validation — sanitizes and validates filenames for file upload/export operations |
| `certifi` | TLS certificates — provides up-to-date root certificates for HTTPS/OIDC provider connections |

## Dev Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing framework — runs unit and integration tests in `backend/tests/` |
| `ruff` | Linting & formatting — enforces code style, import sorting, and error detection |
| `zensical` | Documentation — builds and serves this documentation site |
