import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.general import BaseFilter


class EvaluationTemplateBase(BaseModel):
    """
    Base schema for evaluation templates
    """

    name: str = ""
    evaluation_criteria: str = ""
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "TechinfoAccurate",
                "evaluation_criteria": "Is the technical information provided accurate?",
                "description": "The provided information in the ticket/notification should be accurate.",
            }
        },
    )


class EvaluationTemplateRead(EvaluationTemplateBase):
    """
    Schema for reading evaluation templates
    """

    id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                **EvaluationTemplateBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
            }
        },
    )


class EvaluationTemplateFilter(BaseFilter):
    """
    Schema for filtering evaluation templates
    """

    name: str | None = None
    evaluation_criteria: str | None = None
    description: str | None = None
    sort_by: Literal["name"] | None = None
