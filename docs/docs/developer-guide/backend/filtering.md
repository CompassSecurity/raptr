# Filtering & Sorting

The backend handles pagination, filtering and sorting automatically. To handle this backend logic without writing boilerplate SQL queries for every route, the application uses a centralized set of **Query Utilities**. 

By simply defining a Pydantic "Filter Schema" with strongly typed fields, these utilities can automatically inject the correct SQL `WHERE` clauses (e.g., partial matches for strings, `IN` clauses for lists) and handle the pagination math behind the scenes.

## Response Types

List endpoints return data in one of two formats depending on whether pagination is required.

### 1. Paginated Responses
Most list endpoints return a `PaginatedResponse[T]` wrapper:

```python
# app/schemas/general.py
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]    # The page of results
    total: int        # Total count across all pages
    page: int         # Current page number (1-indexed)
    size: int         # Items per page
    pages: int        # Total number of pages
```

Clients send `offset` and `limit` as query parameters. The response includes calculated metadata.

### 2. Non-Paginated Responses
For endpoints where the client needs the entire dataset at once (e.g., dropdown options), the endpoint returns a standard Python list:
`list[T]`

---

## Filtering and Sorting

Every list endpoint accepts filter and sort parameters through a **filter schema**. Depending on the endpoint type, this schema extends either `BaseFilter` or `BaseModel`.

### Paginated Filter Schemas (`BaseFilter`)

```python
# app/schemas/general.py
class BaseFilter(BaseModel):
    offset: int = 0
    limit: int = 100
    sort_order: Literal["asc", "desc"] | None = None
```

All paginated filter schemas inherit from `BaseFilter` and add:

- **Filter fields** — optional fields matching model columns
- **`sort_by`** — a `Literal` type listing the allowed sort columns

### Non-Paginated Filter Schemas (`BaseModel`)

For non-paginated endpoints (using `query()`), the schema should extend `BaseModel` directly since `limit` and `offset` are not applicable. You must manually define `sort_order` if you want to support sorting.

```python
# app/schemas/report.py
from typing import Literal
from pydantic import BaseModel
from app.enums.enums import ReportTemplateFormat

class ReportTemplateFilter(BaseModel):
    filename: str | None = None
    format: ReportTemplateFormat | None = None
    sort_by: Literal["filename", "format"] = "filename"
    sort_order: Literal["asc", "desc"] = "asc"
```

### Writing a Filter Schema

```python
# app/schemas/widget.py
from typing import Literal
from app.enums.enums import WidgetCategory
from app.schemas.general import BaseFilter

class WidgetFilter(BaseFilter):
    # String filter → case-insensitive partial match (ILIKE %value%)
    name: str | None = None

    # List filter → SQL IN clause (matches any value in the list)
    category: list[WidgetCategory] | None = None

    # Boolean filter → exact match
    active: bool | None = None

    # Sortable fields
    sort_by: Literal["name", "category", "created_at"] | None = None
```

**Filter behavior is automatic based on the Python type:**

| Field type | SQL behavior | Example |
|-----------|-------------|---------|
| `str` | Case-insensitive partial match (`ILIKE %value%`) | `name=foo` matches "Foobar" |
| `list[T]` | `IN` clause (matches any) | `category=Low&category=High` |
| `bool`, `int`, `uuid`, etc. | Exact match (`==`) | `active=true` |

All filter fields must be `Optional` (default `None`). When `None`, the filter is skipped.

### Query Utilities

The generic query helpers in `app/services/utils/query.py` do the heavy lifting:

```python
from app.services.utils.query import paginated_query, query

# Paginated (most list endpoints)
result = paginated_query(session, Widget, filter_query)
# Returns: PaginatedResponse[Widget]

# Non-paginated (when you need all items)
items = query(session, File, filter_query)
# Returns: list[File]
```

Both functions accept the same optional parameters:

| Parameter | Purpose |
|-----------|---------|
| `base_statement` | Pre-built SQLAlchemy select (for custom joins, access control filters) |
| `filter_mapper` | Map filter field names to custom SQLAlchemy columns (for joined columns) |
| `sort_mapper` | Map sort field names to custom SQLAlchemy columns or column lists |
| `exclude_filters` | Set of field names to skip automatic filtering (handle manually) |

### Basic Example (Paginated)

For simple endpoints where filter fields map directly to model columns, no extra config is needed:

```python
def get_all_assessments_service(
    user: User,
    session: Session,
    filter_query: AssessmentFilter,
) -> PaginatedResponse[Assessment]:
    base_statement = select(Assessment)

    # Access control: non-admins only see assessments they have ACL for
    if user.role != UserRole.ADMIN:
        base_statement = base_statement.join(Acl).where(Acl.user_id == user.id)

    return paginated_query(session, Assessment, filter_query, base_statement=base_statement)
```

### Basic Example (Non-Paginated)

If you need to return all matching records without pagination, use the `query` utility. It accepts the exact same parameters as `paginated_query`:

```python
def get_all_tags_service(
    session: Session,
    filter_query: TagFilter,
) -> list[Tag]:
    # Returns a standard list of Tags matching the filter criteria
    return query(session, Tag, filter_query)
```

### Advanced Example — Custom Joins, Mappers, and Excluded Filters

When filter or sort fields don't map directly to the main model, use mappers:

```python
def get_all_activities_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: ActivityFilter,
) -> PaginatedResponse[Activity]:
    # Start with joins needed for filtering/sorting
    statement = (
        select(Activity)
        .filter(Activity.assessment_id == assessment_id)
        .outerjoin(ActivityGroup)
        .outerjoin(ActivityEvaluation)
    )

    # Handle many-to-many filter manually, then exclude from auto-filtering
    exclude_filters = set()
    if filter_query.tags:
        statement = statement.where(Activity.tags.any(Tag.id.in_(filter_query.tags)))
        exclude_filters.add("tags")

    # Map filter/sort fields to joined columns
    filter_mapper = {
        "activity_group_id": Activity.activity_group_id,
    }

    sort_mapper = {
        "activity_group.name": ActivityGroup.name,
        "activity_coverage_score": ActivityEvaluation.activity_coverage_score,
        # Composite sort: sort by group position first, then activity position
        "activity_position": [
            ActivityGroup.activity_group_position,
            Activity.activity_position,
        ],
    }

    return paginated_query(
        session,
        Activity,
        filter_query,
        base_statement=statement,
        filter_mapper=filter_mapper,
        sort_mapper=sort_mapper,
        exclude_filters=exclude_filters,
    )
```

**Key patterns:**

- **Joined column sorting**: Use `sort_mapper` to map a sort name to a column from a joined table
- **Composite sorting**: Pass a list of columns to `sort_mapper` — they are all applied in order with the same direction
- **Many-to-many filters**: Filter manually with `.any()` or `.has()`, then add the field name to `exclude_filters` so the generic filter logic skips it
- **Access control**: Add WHERE clauses to `base_statement` before passing it to `paginated_query`
