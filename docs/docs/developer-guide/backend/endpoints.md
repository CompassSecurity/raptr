# Adding a New Endpoint

Follow the **Model → Schema → Service → Router** pattern:

## Model (`app/models/`)

SQLAlchemy 2.0 models use `Mapped` types. Each entity gets its own file in `app/models/`.

### The `Base` Model

All models must inherit from `app.models.base.Base`, which automatically provides:
- `__tablename__` (auto-generated from the class name)
- Audit fields: `created_at` (datetime), `created_by` (uuid), `updated_at` (datetime), `updated_by` (uuid)

You still need to define the primary key `id` explicitly on each model. We use UUIDs for all primary keys.

??? bug "ID field"
    Writing this guide I wonder why I did not add `id` to the `Base` model...hmm

```python
import uuid
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Widget(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment.id"))
    
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000))
```

### Common Patterns

**1. Soft Deletion**
If records should be archived rather than hard-deleted, use the `SoftDeleteMixin` alongside `Base`:
```python
from app.models.base import Base, SoftDeleteMixin

class Widget(Base, SoftDeleteMixin):
    # Automatically adds: deleted (bool), deleted_at (datetime), deleted_by (uuid)
    # ...
```

**2. Relationships**
Define relationships explicitly using `relationship()`. Always consider cascading behavior.
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import uuid

class Widget(Base):
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment.id"))
    assessment: Mapped["Assessment"] = relationship(back_populates="widgets")
    
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"] = relationship(back_populates="widgets")
```

For **many-to-many** relationships, define an explicit association table:
```python
from sqlalchemy import Column, ForeignKey, Table

widget_tag = Table(
    "widget_tag",
    Base.metadata,
    Column("widget_id", ForeignKey("widget.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)
```

**3. Enums**
Use SQLAlchemy's Enum support for fixed choices. All application enums live in `app/enums/enums.py`.
```python
from sqlalchemy import Enum
from app.enums.enums import WidgetSize

class Widget(Base):
    size: Mapped[WidgetSize]
```

**4. Dynamic Data (JSONB)**
For unstructured or dynamic properties, use PostgreSQL's `JSONB`:
```python
from sqlalchemy.dialects.postgresql import JSONB

class Widget(Base):
    properties: Mapped[dict | list | None] = mapped_column(JSONB)
```

## Schema (`app/schemas/`)

Schemas are Pydantic models that define the shape of request and response data. They provide validation and OpenAPI documentation. Each entity has its own schema file (e.g., `widget.py`), separated into multiple classes by purpose.

### Standard Schema Types

| Schema | Purpose | Inherits from | Used by |
|--------|---------|---------------|---------|
| `WidgetBase` | Shared fields for create/update requests | `BaseModel` | Request body (POST) |
| `WidgetRead` | API response shape | `WidgetBase` | `response_model` on GET/POST/PUT |
| `WidgetUpdate` | Partial update fields | `BaseModel` | Request body (PUT/PATCH) |
| `WidgetCreate` | Create with extra required fields (e.g., password) | `WidgetBase` | Request body (POST) when creation differs from Base |
| `WidgetFilter` | Query parameters for list endpoints | `BaseFilter` | `Query()` on GET endpoints |

Not every entity needs all schema types — only create the ones you need. Most simple entities only require `Base`, `Read`, and `Filter`.

### Common Patterns

**1. Base Schema and Examples**
Define fields required for creation, and always provide an OpenAPI example using `model_config`.
```python
import uuid
from pydantic import BaseModel, ConfigDict
from app.enums.enums import WidgetSize

class WidgetBase(BaseModel):
    name: str
    description: str | None = None
    size: WidgetSize

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My Widget",
                "description": "A very nice widget.",
                "size": "Medium"
            }
        }
    )
```

**2. Read Schema and ORM Parsing**
The `Read` schema represents the database record returned to the client. It must include `from_attributes=True` so Pydantic can directly serialize SQLAlchemy model instances.
```python
class WidgetRead(WidgetBase):
    id: uuid.UUID
    created_at: datetime
    
    # Nested relationship schemas go here
    category: CategoryRead | None = None

    model_config = ConfigDict(
        from_attributes=True,  # Crucial for SQLAlchemy compatibility
        json_schema_extra={
            "example": {
                # Spread the base example to avoid duplication
                **WidgetBase.model_config.get("json_schema_extra", {}).get("example", {}),
                "id": "00000000-0000-0000-0000-000000000000",
                "created_at": "2026-01-01T10:00:00Z"
            }
        },
    )
```

**3. Relationship Handling (IDs vs Objects)**
Write schemas (`Base`/`Update`) expect lists of UUIDs for relationships to avoid complex nested creation logic. Read schemas return nested objects.
```python
class ActivityUpdate(ActivityBase):
    # Expect UUIDs when updating the record
    tags: list[uuid.UUID] = []
    
class ActivityRead(ActivityUpdate):
    # Return full tag objects in the response
    tags: list[TagRead] = []
```

**4. Filter Schemas**
Filter schemas are used for GET list endpoints and must inherit from `BaseFilter` (which provides `limit`, `offset`, and `sort_order`). See the [Filtering and Sorting](filtering.md) section for full details.
```python
from typing import Literal
from app.schemas.general import BaseFilter

class WidgetFilter(BaseFilter):
    name: str | None = None
    size: list[WidgetSize] | None = None
    sort_by: Literal["name", "created_at"] | None = None
```

**5. Specialized Update Schemas**
If a specific user role (like the Blue team) is only allowed to update a subset of fields, create a specialized schema to strictly enforce this at the validation layer.
```python
class ActivityUpdateBlue(BaseModel):
    """Activity update model for Blue users."""
    log_notes: str | None = None
    logged: bool | None = None
    state: ActivityStateBlue | None = ActivityStateBlue.WAITING_BLUE
```

## Service (`app/services/`)

The service layer is the core of the backend architecture. **Routers should contain zero business logic.** All database queries, relationship assignments, and specialized business rules belong in services.

### Common Patterns

**1. Standard CRUD Methods**
Name your service functions consistently: `get_all_X_service`, `get_X_by_id_service`, `create_X_service`, `update_X_service`, and `delete_X_service` (or `toggle_delete_X_service`).

```python
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.models.widget import Widget
from app.models.user import User
from app.schemas.widget import WidgetUpdate

def get_widget_by_id_service(
    widget_id: uuid.UUID, 
    assessment_id: uuid.UUID,
    user: User,
    session: Session
) -> Widget:
    # Validate that the assessment exists and the user has access to it
    from app.services.assessment.assessment import get_assessment_by_id_service
    get_assessment_by_id_service(assessment_id, user, session)

    # Use SQLAlchemy 2.0 syntax (select, scalars, one_or_none)
    statement = select(Widget).where(
        Widget.id == widget_id,
        Widget.assessment_id == assessment_id,
        Widget.deleted.is_(False)
    )
    widget = session.execute(statement).scalars().unique().one_or_none()
    
    # 404s are raised directly from the service
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Widget not found"
        )
    return widget

def update_widget_service(
    widget_id: uuid.UUID, 
    update_data: WidgetUpdate, 
    assessment_id: uuid.UUID,
    user: User,
    session: Session
) -> Widget:
    widget = get_widget_by_id_service(widget_id, assessment_id, user, session)

    # Apply Pydantic model fields to SQLAlchemy model
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(widget, field, value)

    # Audit fields update
    widget.updated_by = user.id
    widget.updated_at = func.now()
    # The service is responsible for committing the transaction
    session.commit()
    session.refresh(widget)
    return widget
```

**2. List Endpoints (`paginated_query` and `query`)**
List endpoints delegate filtering, sorting, and pagination logic to the `paginated_query` (or `query` for flat lists) utility functions. You can optionally provide a `base_statement` to enforce mandatory filters (like role-based visibility). See [Filtering and Sorting](filtering.md#query-utilities) for full details on both.

```python
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.enums.enums import AclRole
from app.models.user import User
from app.models.widget import Widget
from app.schemas.general import PaginatedResponse
from app.services.utils.query import paginated_query
from app.schemas.widget import WidgetFilter

def get_all_widgets_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: WidgetFilter,
) -> PaginatedResponse[Widget]:
    # Validate that the assessment exists and the user has access to it
    from app.services.assessment.assessment import get_assessment_by_id_service
    get_assessment_by_id_service(assessment_id, user, session)

    statement = select(Widget).filter(Widget.assessment_id == assessment_id)

    # Example: Hide soft-deleted and non-visible items for non-RED users (e.g., Blue team)
    if user.assessment_acl_role != AclRole.RED:
        statement = statement.where(
            Widget.deleted.is_(False),
            Widget.visible.is_(True)
        )

    return paginated_query(
        session, 
        Widget, 
        filter_query,
        base_statement=statement
    )
```

**3. Service Design Principles**

- **The `User` Object:** Every service method should accept the `user: User` object passed down from the router. This provides crucial context:
  - `user.id` — for audit fields (`created_by`, `updated_by`).
  - `user.assessment_acl_role` — the user's role in the current assessment (e.g., `AclRole.RED` or `AclRole.BLUE`). Use this to enforce row-level visibility or restrict which fields can be edited logic directly in the service.
- **Centralized Validation (`get_by_id`):** We use a strict pattern where the `get_X_by_id_service` method acts as the gatekeeper for all other operations (update, delete, etc.). This function handles checking if the record exists, if it belongs to the correct parent (like `assessment_id`), and if the current user has the right ACL visibility. By calling this method first in your `update` or `delete` services, you ensure the 404 Not Found or visibility errors are defined and raised in exactly one place.
```python
def update_activity_service(activity_id, activity_update, assessment_id, user, session):
    # This single call acts as the validator: it will throw a 404 if the 
    # activity doesn't exist, belongs to another assessment, or is hidden 
    # from a Blue team user. You do not need to rewrite the checks here!
    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)
    
    # ... proceed with updating activity_db ...
```

## Router (`app/api/v1/`)

Routers define the HTTP API contract. They handle request parsing, dependency injection, and response formatting, but delegate all business logic to the Service layer.

### Example Router

```python
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.general import MessageResponse, PaginatedResponse
from app.schemas.widget import WidgetFilter, WidgetRead
from app.services.widget import get_all_widgets_service, toggle_delete_widget_service

router = APIRouter(prefix="/widgets", tags=["widgets"])

@router.get("/", response_model=PaginatedResponse[WidgetRead])
def list_widgets(
    assessment_id: uuid.UUID,
    filter_query: Annotated[WidgetFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Get all widgets for an assessment.
    """
    return get_all_widgets_service(assessment_id, user, session, filter_query)

@router.put("/{widget_id}/delete", response_model=MessageResponse)
def toggle_delete_widget(
    widget_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Toggle the deleted state of a widget.
    """
    toggle_delete_widget_service(widget_id, assessment_id, user, session)
    return MessageResponse(message="Widget deleted state toggled successfully")
```

Register the new router in `app/api/v1/router.py`.

### Router Design Principles

**1. Standardized Responses (`PaginatedResponse` & `MessageResponse`)**
Always use strongly typed response models from `app.schemas.general` (or standard Python lists).

- For paginated list endpoints, return `PaginatedResponse[T]`.
- For non-paginated list endpoints (using `query`), return a standard `list[T]`.
- For action endpoints that don't return an entity (like delete, toggle status), return a `MessageResponse(message="...")` explicitly in the router after calling the service.

**2. Dependency Injection**
Almost every route requires the current `User` and a database `Session`.

- `session: Session = Depends(get_session)` — Provides a transaction-scoped database session.
- `user: User = Depends(require_assessment_role(AclRole.RED))` — Authenticates the user and verifies they have the required role for the given `assessment_id` in the URL/body.

**3. Access Control (ACL) Options**
The authentication layer provides several dependencies depending on the required authorization level. (See the [Authentication & Authorization](auth.md) guide for full details).

*Global Authorization:*

- `get_current_active_user`: Validates the JWT and ensures the user account is active.
- `mfa_validation_service`: Extends the active user check by also verifying the user has completed MFA setup (if required by their configuration).
- `admin_role_validation_service`: Restricts an endpoint globally to users with `UserRole.ADMIN`.

*Assessment-Level Authorization:*

- `require_assessment_role(AclRole.SPECTATOR)`: Read-only access to the assessment.
- `require_assessment_role(AclRole.BLUE)`: Blue team access (can update specific fields like `log_time`).
- `require_assessment_role(AclRole.RED)`: Full RED team access (can create, edit, delete).
- `validate_activity_update_permission`: A custom dependency that adapts to the user's role specifically for activity updates.

**4. Zero Business Logic**
Routers should only map HTTP inputs (Path, Query, Body parameters) to Python types, inject dependencies, and call a single service method. Do not write `if/else` business rules or database queries in the router.

Register the router in `app/api/v1/router.py`.

---

## Enums

All enums live in `app/enums/enums.py`. They inherit from `(str, enum.Enum)` so they serialize cleanly to JSON.

```python
# app/enums/enums.py
import enum

class ActivityPriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
```

**Available enums:**

| Enum | Values | Used by |
|------|--------|---------|
| `UserRole` | `admin`, `user` | User model |
| `AclRole` | `red`, `blue`, `spectator` | ACL model |
| `AssessmentType` | `PurpleTeam`, `RedTeam` | Assessment model |
| `ActivityState` | `Pending`, `Waiting Red`, `Waiting Blue`, `Ready`, `In Progress`, `In Evaluation`, `Completed`, `Cancelled` | Activity model |
| `ActivityPriority` | `Low`, `Medium`, `High`, `Critical` | Activity model |
| `ActivitySeverity` | `Informational`, `Low`, `Medium`, `High`, `Critical` | Activity model |
| `ActivityAssetRole` | `source`, `target`, `tool`, `log_source`, ... | Activity-Asset association |
| `EvaluationResult` | `pass`, `fail`, `n/a` | Evaluation model |
| `ReportTemplateFormat` | `html`, `docx` | Report templates |
| `FileCategory` | `red`, `blue` | File model |
| `FileType` | `image/png`, `image/jpeg`, `image/jpg`, `text/plain` | File model |
| `CampaignTemplateItemType` | `group`, `activity` | Campaign templates |

When adding a new enum, add it to `app/enums/enums.py` and import from there. Use enums in models, schemas, and filters — never use raw strings for fixed option sets.
