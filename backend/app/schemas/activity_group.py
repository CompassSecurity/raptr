import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ActivityGroupFilter(BaseModel):
    """
    Filter schema for activity group queries.
    Inherits from BaseModel because it is not paginated.
    """

    name: str | None = None
    activity_group_position: int | None = None
    sort_by: (
        Literal[
            "name",
            "activity_group_position",
        ]
        | None
    ) = None
    sort_order: Literal["asc", "desc"] | None = None


class ActivityGroupBase(BaseModel):
    """
    Shared properties for activity groups
    """

    name: str
    visible: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Example Activity Group", "visible": False}
        },
    )


class ActivityGroupRead(ActivityGroupBase):
    """
    Properties to return via API
    """

    id: uuid.UUID
    deleted: bool
    is_default: bool
    activity_group_position: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **ActivityGroupBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
                "deleted": False,
                "is_default": False,
                "activity_group_position": 0,
            }
        },
    )


class ActivityGroupReorder(BaseModel):
    """
    Schema for reordering activities within a activity group
    """

    activity_group_ids: list[uuid.UUID]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "activity_group_ids": [
                    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "a8098c1a-f86e-11da-bd1a-00112444be1e",
                ]
            }
        }
    )


class ActivityReorder(BaseModel):
    """
    Schema for reordering activities within a activity group
    """

    activity_ids: list[uuid.UUID]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "activity_ids": [
                    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "a8098c1a-f86e-11da-bd1a-00112444be1e",
                ]
            }
        }
    )


class ActivityGroupUpdate(BaseModel):
    """
    Schema for assigning/updating an activity's group
    """

    activity_group_id: uuid.UUID | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"activity_group_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}
        }
    )
