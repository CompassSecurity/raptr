from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.schemas.general import PaginatedResponse

T = TypeVar("T")  # SQLAlchemy model type


def apply_filters_and_sorting(
    model: type[T],
    filter_query: BaseModel,
    base_statement=None,
    filter_mapper: dict[str, Any] | None = None,
    sort_mapper: dict[str, Any] | None = None,
    exclude_filters: set[str] | None = None,
):
    """
    Helper function to apply filters and sorting to a base statement.
    """
    if base_statement is None:
        base_statement = select(model)

    # Fields that are pagination/sorting, not filters
    exclude_fields = {"offset", "limit", "sort_by", "sort_order"}
    if exclude_filters:
        exclude_fields.update(exclude_filters)

    filter_mapper = filter_mapper or {}
    sort_mapper = sort_mapper or {}

    # Apply filters
    for field, value in filter_query.model_dump(exclude_none=True).items():
        if field in exclude_fields:
            continue

        column = filter_mapper.get(field, getattr(model, field, None))

        if column is None:
            continue

        # String fields: case-insensitive partial match
        if isinstance(value, str):
            escaped = (
                value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            base_statement = base_statement.where(
                column.ilike(f"%{escaped}%", escape="\\")
            )
        # List fields: use IN clause
        elif isinstance(value, list):
            base_statement = base_statement.where(column.in_(value))
        # Other types: exact match
        else:
            base_statement = base_statement.where(column == value)

    # Apply sorting
    sort_by = getattr(filter_query, "sort_by", None)
    sort_order = getattr(filter_query, "sort_order", None)
    if sort_by and sort_order:
        sort_column = sort_mapper.get(sort_by, getattr(model, sort_by, None))
        if sort_column is not None:
            if isinstance(sort_column, (list, tuple)):
                if sort_order == "desc":
                    base_statement = base_statement.order_by(
                        *(col.desc() for col in sort_column)
                    )
                else:
                    base_statement = base_statement.order_by(
                        *(col.asc() for col in sort_column)
                    )
            else:
                if sort_order == "desc":
                    base_statement = base_statement.order_by(sort_column.desc())
                else:
                    base_statement = base_statement.order_by(sort_column.asc())

    return base_statement


def query(
    session: Session,
    model: type[T],
    filter_query: BaseModel,
    base_statement=None,
    filter_mapper: dict[str, Any] | None = None,
    sort_mapper: dict[str, Any] | None = None,
    exclude_filters: set[str] | None = None,
) -> list[T]:
    """
    Generic filterable, sortable query (non-paginated).

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class (e.g., User, ActivityTemplate)
        filter_query: Pydantic model with filter fields + sort_by, sort_order
        base_statement: Optional pre-built statement (for custom joins/filters)
        filter_mapper: Map filter fields to SQLAlchemy columns
        sort_mapper: Map sort fields to SQLAlchemy columns
        exclude_filters: Fields to skip generic filtering

    Returns:
        List of items
    """
    statement = apply_filters_and_sorting(
        model,
        filter_query,
        base_statement,
        filter_mapper=filter_mapper,
        sort_mapper=sort_mapper,
        exclude_filters=exclude_filters,
    )
    return session.execute(statement).scalars().unique().all()


def paginated_query(
    session: Session,
    model: type[T],
    filter_query: BaseModel,
    base_statement=None,
    filter_mapper: dict[str, Any] | None = None,
    sort_mapper: dict[str, Any] | None = None,
    exclude_filters: set[str] | None = None,
) -> PaginatedResponse[T]:
    """
    Generic paginated, filterable, sortable query.

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class (e.g., User, ActivityTemplate)
        filter_query: Pydantic model with filter fields + offset, limit, sort_by, sort_order
        base_statement: Optional pre-built statement (for custom joins/filters)
        filter_mapper: Map filter fields to SQLAlchemy columns
        sort_mapper: Map sort fields to SQLAlchemy columns
        exclude_filters: Fields to skip generic filtering

    Returns:
        PaginatedResponse with items and pagination metadata

    Example:
        class UserFilter(BaseModel):
            email: str | None = None
            role: list[UserRole] | None = None
            offset: int = 0
            limit: int = 100
            sort_by: Literal["email", "role"] | None = None
            sort_order: Literal["asc", "desc"] | None = None

        result = paginated_query(session, User, filter_query)
    """
    base_statement = apply_filters_and_sorting(
        model,
        filter_query,
        base_statement,
        filter_mapper=filter_mapper,
        sort_mapper=sort_mapper,
        exclude_filters=exclude_filters,
    )

    # Get total count
    count_statement = select(func.count()).select_from(base_statement.subquery())
    total = session.execute(count_statement).scalar() or 0

    # Get pagination params
    offset = getattr(filter_query, "offset", 0)
    limit = getattr(filter_query, "limit", 100)

    # Get paginated items
    statement = base_statement.offset(offset).limit(limit)
    items = session.execute(statement).scalars().unique().all()

    # Calculate pagination metadata
    page = (offset // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages,
    )
