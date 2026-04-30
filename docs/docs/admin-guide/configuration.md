# Configuration

RAPTR is configured entirely through environment variables, read from a `.env` file at `backend/.env`. All settings use [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) and can be overridden via environment variables.

The in-app [configuration page](../user-guide/administration.md#view-system-configuration) at `/admin/configuration` displays all current settings (read-only).

## Environment Variable Reference

### General

| Variable | Default | Description |
|---|---|---|
| `APPLICATION_NAME` | `RAPTR` | Name used for JWT tokens as `iss` and `aud` claims, as MFA issuer during TOTP setup and as logger name |
| `LOG_LEVEL` | `INFO` | Python logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `FASTAPI_DOCUMENTATION` | `true` | Enable the OpenAPI documentation at `/docs` and `/redoc`. Set to `false` in production to hide the API docs |

??? bug "Inconsistent Logging"
    The implemented logging requires a rework. Not all relevant logs are created or stored in the DB (audit trail).

### Admin Account

| Variable | Default | Description |
|---|---|---|
| `ADMIN_EMAIL` | `admin@raptr.app` | Email address for the default admin account. Created on first launch |
| `ADMIN_PASSWORD` | *(auto-generated)* | Password for the default admin account. If not set, a 32-character password is generated and written to `.env` on first launch |


### Security

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(auto-generated)* | Secret key for signing JWT tokens. If not set, a 64-character hex key is generated and written to `.env` on first launch |
| `MIN_PASSWORD_LENGTH` | `8` | Minimum password length for user accounts. A floor of `4` is enforced regardless of this value |
| `OTP_LOCAL_ENABLED` | `true` | Enable TOTP-based multi-factor authentication for local users. When enabled, local users must set up an authenticator app |
| `OTP_EXTERNAL_ENABLED` | `false` | Enable TOTP-based multi-factor authentication for external IdP users. When enabled, external users must complete MFA after IdP login |

??? info "Password complexity"
    Currently, you can only configure the minimum password length. You cannot define complexity requirements. RAPTR always enforces the following rules:

    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one digit
    - Must contain at least one special character

### CORS Settings

| Variable | Default | Description |
|---|---|---|
| `CORS_ENABLED` | `false` | Set to `true` to enable Cross-Origin Resource Sharing. Must be `true` for other CORS settings to apply. |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://127.0.0.1:5173"]` | JSON array of allowed origins for CORS. |
| `CORS_METHODS` | `["GET", "POST", "PUT", "DELETE"]` | JSON array of allowed HTTP methods for CORS. |
| `CORS_HEADERS` | `["*"]` | JSON array of allowed headers for CORS. |
| `CORS_CREDENTIALS` | `true` | Boolean to indicate if cross-origin requests support credentials. |
| `CORS_MAX_AGE` | `600` | Maximum age in seconds to cache preflight requests. |

### Database

| Variable | Default | Description |
|---|---|---|
| `DB_ENGINE` | `postgres` | Database engine to use: `postgres` or `sqlite` |
| `SQLITE_DB_PATH` | `raptr.db` | Path to the SQLite database file. Only used if `DB_ENGINE=sqlite` |
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | `postgres` | PostgreSQL database name |
| `POSTGRES_HOST` | `localhost` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |

The PostgreSQL connection string is assembled as: `postgresql+psycopg://{user}:{password}@{host}:{port}/{db}`

For SQLite, it is assembled as: `sqlite:///{SQLITE_DB_PATH}`

??? tip "Use PostgreSQL"
    RAPTR is designed to use PostgreSQL. Support for SQLite is merely a courtesy.

### JWT

| Variable | Default | Description |
|---|---|---|
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT token validity period in minutes |

??? info "No Refresh Tokens"
    RAPTR does not have refresh tokens for local authentication. Therefore, users **must** log in again after their access token has expired. Explicitly logging out invalidates all access tokens. Select a value for `ACCESS_TOKEN_EXPIRE_MINUTES` that represents the desired hard session timeout.

### TLS / HTTPS

??? warning "Affects container image only"
    This setting only affects the container image and is not part of the FastAPI configuration.

| Variable | Default | Description |
|---|---|---|
| `TLS_ENABLED` | `true` | Set to `false` to serve plain HTTP instead of HTTPS. When `true`, the entrypoint generates a self-signed certificate if no certificate files are found at `/app/certs/` |

When TLS is enabled, the container looks for `/app/certs/cert.pem` and `/app/certs/key.pem`. If they are missing, a self-signed certificate is auto-generated. To use your own certificates, mount them via the `docker-compose.yml` volume:

```yaml
volumes:
  - ./certs:/app/certs
```


### External Data Sources

| Variable | Default | Description |
|---|---|---|
| `MITRE_JSON_URL` | `https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json` | URL to the MITRE ATT&CK enterprise JSON file. Used when seeding MITRE data from the admin panel |
| `ATOMIC_RED_TEAM_URL` | `https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip` | URL to the Atomic Red Team repository ZIP. Used when seeding ART activity templates |
| `CUSTOM_DATA_URL` | *(none)* | URL to your organization's custom data repository ZIP. See [Custom Data & Templates](custom_data.md) |
| `CUSTOM_DATA_TOKEN` | *(none)* | Bearer token (e.g., GitHub PAT) for accessing private custom data repositories |

??? tip "GitHub ZIP URLs"
    The ZIP URLs for GitHub repositories are in the format: `https://api.github.com/repos/{owner}/{repo}/zipball/{branch}`

??? tip "GitLab repository ZIP URLs"
    The ZIP URLs for GitLab repositories are in the format: `https://gitlab.com/api/v4/projects/{project_id}/repository/archive.zip`

### External Authentication

| Variable | Default | Description |
|---|---|---|
| `EXTERNAL_AUTH_CONFIGS` | `[]` | JSON array of external OAuth/OIDC provider configurations. See [External Authentication](external_authentication.md) |

## Example `.env` File

```env
# Application
APPLICATION_NAME=RAPTR-YourOrg
LOG_LEVEL=INFO
FASTAPI_DOCUMENTATION=false
CORS_ENABLED=false

# Admin account
ADMIN_EMAIL=admin@your-org.something
# ADMIN_PASSWORD will be auto-generated on first launch

# Database
DB_ENGINE=postgres
POSTGRES_USER=raptr-db-user
POSTGRES_PASSWORD=a-very-strong-password-here
POSTGRES_DB=raptr
POSTGRES_HOST=db.your-org.something
POSTGRES_PORT=5432

# Security
MIN_PASSWORD_LENGTH=12
# SECRET_KEY will be auto-generated on first launch

# External data sources
CUSTOM_DATA_URL=https://api.github.com/repos/your-org/raptr-templates/zipball/main
CUSTOM_DATA_TOKEN=ghp_your_github_pat_here

# External authentication (JSON array)
EXTERNAL_AUTH_CONFIGS='[
  {
    "name": "Entra ID",
    "configuration": "https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration",
    "issuer": "https://login.microsoftonline.com/{tenant-id}/v2.0",
    "jwks_url": "https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys",
    "audience": "your-client-id",
    "scope": "api://{App-registration-for-backend}/api",
    "client_id": "your-client-id",
    "username_claim": "preferred_username",
    "trusted_email_domains": [
      "your-org.something"
    ]
  }
]'
```