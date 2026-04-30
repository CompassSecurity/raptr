import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.general import BaseFilter


class ActivityGroupTemplateRead(BaseModel):
    """
    Activity group template read model
    """

    id: uuid.UUID
    name: str
    description: str | None = None
    activity_template_ids: list[uuid.UUID] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "Group 1",
                "description": "Description 1",
                "activity_template_ids": ["00000000-0000-0000-0000-000000000000"],
            }
        },
    )


class ActivityGroupTemplateFilter(BaseFilter):
    """
    Filter schema for activity group template queries. All fields optional.
    """

    name: str | None = None
    sort_by: Literal["name"] | None = None
