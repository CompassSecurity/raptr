import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.general import BaseFilter


class CampaignTemplateItemRead(BaseModel):
    """
    Campaign template item read model
    """

    id: uuid.UUID
    position: int
    item_type: str
    activity_group_template_id: uuid.UUID | None = None
    activity_template_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CampaignTemplateRead(BaseModel):
    """
    Campaign template read model
    """

    id: uuid.UUID
    name: str
    description: str | None = None
    items: list[CampaignTemplateItemRead] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "Standard AD Campaign",
                "description": "Standard Active Directory assessment campaign",
                "items": [],
            }
        },
    )


class CampaignTemplateFilter(BaseFilter):
    """
    Filter schema for campaign template queries. All fields optional.
    """

    name: str | None = None
    sort_by: Literal["name"] | None = None
