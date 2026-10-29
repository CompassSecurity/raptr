# Logging

RAPTR writes its log to **stdout** with a single application logger. The log is meant to answer *who changed what and when*, and to show security-relevant events and errors.

```python
from app.core.logging import app_logger
```

The logger is named after `APPLICATION_NAME` and filtered by `LOG_LEVEL` (see [Configuration](../../admin-guide/configuration.md#general)). Each line looks like this:

```
[2026-10-29 14:03:12,511] INFO in RAPTR: User admin@raptr.app deleted activity 'Kerberoasting' (4f0c…) in assessment 9b2e…
```

Uvicorn writes its own lines (startup, one access line per request) in its own format next to the application log.

## Where to Log

| Layer | Logs | Examples |
|---|---|---|
| **Services** (`app/services/`) | Business events: one line per successful write, plus rejected actions that matter | assessment created, ACL changed, activity deleted, report generated, import finished |
| **Core** (`app/core/`) | Security events | login, logout, MFA, token validation, authorization (403) |
| **Routers** (`app/api/`) | Nothing | — the router only calls the service, and Uvicorn's access log already shows every request |

Read operations (`get_*`, lists) are not logged.

## Log Levels

| Level | Use for | Examples |
|---|---|---|
| `ERROR` | Something broke and an operator has to look at it | DB commit failed, download of seed data failed, broken or malicious report template |
| `WARNING` | Expected but security-relevant or suspicious; the request is rejected | failed login, 403, invalid token, rejected upload, invalid import file, single file skipped during seeding |
| `INFO` | A successful state change, one line per action | login, assessment created, tag deleted, file uploaded, seed import started/finished |
| `DEBUG` | Details for troubleshooting | lookups, successful token validation, intermediate steps |

Inside an `except` block, use `app_logger.exception(...)` for unexpected errors. It logs at `ERROR` and adds the traceback. For known errors where the message is enough (e.g. a network error), `app_logger.error(...)` is fine.

## Writing a Log Line

Log **after** `session.commit()`, so only changes that were actually saved show up. Start with the acting user, then the action and the object:

```python
def toggle_delete_widget_service(widget_id, assessment_id, user, session):
    widget = get_widget_by_id_service(widget_id, assessment_id, user, session)
    widget.deleted = not widget.deleted
    session.commit()
    app_logger.info(
        "User %s %s widget '%s' (%s) in assessment %s",
        user.email,
        "deleted" if widget.deleted else "restored",
        widget.name,
        widget.id,
        assessment_id,
    )
```

- **Identify users by email** (`user.email`). Admins can't read UUIDs.
- **Objects by name and id:** `'<name>' (<id>)`. Read the name *before* a hard delete.
- **Use `%` arguments**, not f-strings: `app_logger.info("… %s", value)`. The message is only formatted when the level is enabled.
- **Background jobs without a user** (e.g. startup) log `system` as the actor.

!!! danger "Never log secrets"
    Never pass passwords, tokens, MFA secrets, file contents or whole request bodies to the logger.
