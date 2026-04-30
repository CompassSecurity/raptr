import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.general import BaseFilter


class TagBase(BaseModel):
    """
    Shared properties for multiple tag schemas
    """

    name: str
    color: str = Field(
        ...,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        description="Hex color code (e.g., #FF0000 or #F00)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "ToDo",
                "color": "#FF0000",
            }
        },
    )


class TagRead(TagBase):
    """
    Properties to return via API for general tag requests
    """

    id: uuid.UUID
    deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **TagBase.model_config.get("json_schema_extra", {}).get("example", {}),
                "id": "00000000-0000-0000-0000-000000000000",
                "deleted": False,
            }
        },
    )


class ActivityTagsUpdate(BaseModel):
    """
    Schema for updating activity tags
    """

    tag_ids: list[uuid.UUID] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tag_ids": [
                    "11111111-1111-1111-1111-111111111111",
                    "22222222-2222-2222-2222-222222222222",
                ],
            }
        },
    )


class TagFilter(BaseFilter):
    """
    Filter schema for tag queries. All fields optional.
    """

    name: str | None = None
    deleted: bool | None = None
    sort_by: Literal["name", "color", "deleted"] | None = None
