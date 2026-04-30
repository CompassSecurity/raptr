import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.general import BaseFilter


class AssetBase(BaseModel):
    """
    Asset base model
    """

    name: str
    icon: str | None = None
    properties: dict | None = Field(
        default=None,
        description="Dynamic key-value properties for the asset",
        json_schema_extra={
            "example": {
                "computer_name": "computer1",
                "ip": "192.168.1.1",
                "mac": "00:11:22:33:44:55",
            }
        },
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Test Computer",
                "icon": "Computer",
                "properties": {
                    "computer_name": "computer1",
                    "ip": "192.168.1.1",
                    "mac": "00:11:22:33:44:55",
                },
            }
        }
    )


class AssetRead(AssetBase):
    """
    Asset read model
    """

    id: uuid.UUID
    deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **AssetBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
                "assessment_id": "11111111-1111-1111-1111-111111111111",
                "deleted": False,
            }
        },
    )


class ActivityAssetUpdate(BaseModel):
    """
    Schema for updating activity assets
    """

    asset_ids: list[uuid.UUID]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_ids": [
                    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                ]
            }
        }
    )


class AssetFilter(BaseFilter):
    """
    Filter schema for asset queries.
    """

    name: str | None = None
    deleted: bool | None = None
    sort_by: Literal["name", "deleted"] | None = None
