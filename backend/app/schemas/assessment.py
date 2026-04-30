import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.enums.enums import AssessmentType
from app.schemas.general import BaseFilter


class AssessmentBase(BaseModel):
    """
    Shared properties for multiple assessment schemas
    """

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    assessment_type: AssessmentType = AssessmentType.PurpleTeam

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Purple Team Assessment Example",
                "description": "Atomic based Purple Team engagement",
                "assessment_type": AssessmentType.PurpleTeam,
            }
        },
    )


class AssessmentRead(AssessmentBase):
    """
    Properties to return via API for general assessment requests
    """

    id: uuid.UUID
    default_evaluation_templates: list[dict[str, str | int]]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **AssessmentBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
                "default_evaluation_templates": [
                    {
                        "evaluation_template_id": "00000000-0000-0000-0000-000000000000",
                        "position": 0,
                    }
                ],
            }
        },
    )


class AssessmentFilter(BaseFilter):
    """
    Filter schema for assessment queries. All fields optional.
    """

    name: str | None = None
    assessment_type: list[AssessmentType] | None = None
    sort_by: Literal["name", "assessment_type", "description"] | None = None
