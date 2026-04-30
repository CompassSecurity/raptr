from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseFilter(BaseModel):
    """
    Base filter schema with common pagination and sort order fields.
    Subclasses should add their own filter fields and sort_by with appropriate Literal types.
    """

    offset: int = 0
    limit: int = 100
    sort_order: Literal["asc", "desc"] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper for list endpoints
    """

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class MessageResponse(BaseModel):
    """
    Standard message response
    """

    message: str


class MFASetupResponse(BaseModel):
    """
    Response for MFA setup containing provisioning URI
    """

    provisioning_uri: str
    message: str
