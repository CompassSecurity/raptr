# Backend Development

The backend is a FastAPI application using SQLAlchemy 2.0 for the ORM and Pydantic v2 for validation.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) — Python package manager

## Dev Setup

```bash
cd backend
uv sync              # Install dependencies
uv run fastapi dev   # Start dev server with auto-reload (port 8000)
```

The dev server runs at `http://localhost:8000`. Interactive API docs are available at `/docs` (Swagger) and `/redoc`.

For the full local development setup (including frontend, database, and CORS configuration), see [Deployment → Running Locally](../../admin-guide/deployment.md#running-locally-development).

## Project Structure

```
backend/app/
├── main.py                          # FastAPI app setup and lifespan hooks
├── api/v1/
│   ├── router.py                    # Main router aggregating all endpoints
│   ├── acl/                         # ACL management
│   ├── activity_group_template/     # Activity group template CRUD
│   ├── activity_template/           # Activity template CRUD
│   ├── admin/                       # Admin-only operations (user management)
│   ├── assessment/                  # Single assessment CRUD
│   ├── assessments/                 # Assessment-scoped nested resources
│   │   ├── assessments_router.py    #   Sub-router aggregating nested routes
│   │   ├── activity.py              #   Activities within assessments
│   │   ├── activity_group.py        #   Activity groups
│   │   ├── asset.py                 #   Assets
│   │   ├── tag.py                   #   Tags
│   │   ├── exports.py               #   Export functionality
│   │   ├── imports.py               #   Import functionality
│   │   └── statistics.py            #   Assessment statistics
│   ├── auth/                        # Authentication (login, MFA, OIDC)
│   ├── campaign_template/           # Campaign template CRUD
│   ├── evaluation_template/         # Evaluation template CRUD
│   ├── health/                      # Health check endpoint
│   ├── knowledge_base/              # Knowledge base CRUD
│   ├── mitre/                       # MITRE ATT&CK integration
│   ├── report_template/             # Report template CRUD
│   └── user/                        # User profile and self-management
├── core/
│   ├── authentication.py            # JWT creation, login, OIDC providers
│   ├── authorization.py             # ACL enforcement and role dependencies
│   ├── config.py                    # Pydantic settings (env vars)
│   ├── exceptions.py                # Custom exception handlers
│   ├── logging.py                   # Application logger
│   ├── mfa.py                       # MFA/TOTP validation and setup
│   ├── password.py                  # Password hashing utilities
│   ├── startup.py                   # DB init, admin user creation
│   └── token_validation.py          # JWT decode (internal + external tokens)
├── enums/
│   └── enums.py                     # All application enums
├── frontend/
│   └── frontend.py                  # Serves built Vue SPA in production
├── models/                          # SQLAlchemy ORM models (one file per entity)
│   ├── base.py                      #   Base model with audit fields
│   └── ...                          #   acl, activity, assessment, asset, user, etc.
├── schemas/                         # Pydantic request/response schemas
│   ├── general.py                   #   BaseFilter, PaginatedResponse, MessageResponse
│   └── ...                          #   One file per domain (mirrors models/)
├── services/                        # Business logic (organized by domain)
│   ├── assessment/                  #   Assessment CRUD + export/import
│   ├── activity/                    #   Activity operations
│   ├── report/                      #   Report generation + DOCX markdown rendering
│   │   ├── report.py
│   │   ├── report_data.py
│   │   ├── render.py
│   │   └── markdown.py
│   ├── seed/                        #   Data seeding (MITRE, ART, custom)
│   ├── ...                          #   One folder per domain (mirrors models/)
│   └── utils/                       #   Shared utilities
│       ├── query.py                 #     Generic query, filter, sort, pagination
│       ├── evaluation.py            #     Evaluation helper functions
│       ├── memory.py                #     Memory usage utilities
│       └── position.py              #     Ordering/position utilities
└── db/
    └── session.py                   # Database session management
```

## Dependencies

All dependencies are managed via [uv](https://docs.astral.sh/uv/) and defined in `pyproject.toml`.

### Runtime Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi[standard]` | Web framework — includes Uvicorn, Starlette, and standard extras (CORS, form parsing, etc.) |
| `sqlalchemy` | ORM — database models, queries, and relationships using SQLAlchemy 2.0+ `Mapped` types |
| `pydantic-settings` | Configuration management — loads settings from environment variables with type validation |
| `psycopg` / `psycopg-binary` | PostgreSQL adapter — async-capable driver for production database connections |
| `pyjwt[crypto]` | JWT handling — token creation, validation, and cryptographic signing (RS256/HS256) |
| `pyotp` | TOTP/MFA — generates and validates time-based one-time passwords for multi-factor authentication |
| `pwdlib[argon2]` | Password hashing — secure password storage using the Argon2 algorithm |
| `jinja2` | Templating — used by the report generator to populate dynamic data into both HTML and DOCX report templates |
| `docxtpl` | DOCX report generation — renders Word documents from Jinja2-based templates |
| `markdown-it-py` | Markdown parsing — parses markdown fields to generate native Word paragraphs (OOXML) for DOCX reports |
| `pyyaml` | YAML parsing — used for reading structured data files (MITRE ATT&CK, custom seed data) |
| `pathvalidate` | Path validation — sanitizes and validates filenames for file upload/export operations |
| `certifi` | TLS certificates — provides up-to-date root certificates for HTTPS/OIDC provider connections |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing framework — runs unit and integration tests in `backend/tests/` |
| `ruff` | Linting & formatting — enforces code style, import sorting, and error detection |
| `zensical` | Documentation — builds and serves this documentation site |
