import uuid

from pydantic import BaseModel, ConfigDict

from app.enums.enums import AclRole


class AclBase(BaseModel):
    """
    Shared properties for multiple acl schemas
    """

    assessment_role: AclRole = AclRole.SPECTATOR
    user_id: uuid.UUID
    assessment_id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assessment_role": AclRole.SPECTATOR,
                "user_id": "00000000-0000-0000-0000-000000000004",
                "assessment_id": "10000000-0000-0000-0000-000000000001",
            }
        },
    )


class AclRead(AclBase):
    """
    Properties to return via API for general acl requests
    """

    id: uuid.UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **AclBase.model_config.get("json_schema_extra", {}).get("example", {}),
                "id": "50000000-0000-0000-0000-000000000001",
            }
        },
    )
