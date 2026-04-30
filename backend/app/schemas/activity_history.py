import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBase


class ActivityHistoryBase(BaseModel):
    activity_id: uuid.UUID
    version: int
    saved_at: datetime
    saved_by_id: uuid.UUID | None
    snapshot: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "activity_id": "00000000-0000-0000-0000-000000000000",
                "version": 1,
                "saved_at": "2026-01-01T10:00:00Z",
                "saved_by_id": "11111111-1111-1111-1111-111111111111",
                "snapshot": {"name": "Test Activity"},
            }
        },
    )


class ActivityHistoryRead(ActivityHistoryBase):
    """
    Schema for reading a specific activity history, including the full snapshot.
    """

    id: uuid.UUID
    saved_by: UserBase | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **ActivityHistoryBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "saved_by": {
                    "email": "user@raptr.app",
                    "role": "user",
                    "disabled": False,
                },
            }
        },
    )
