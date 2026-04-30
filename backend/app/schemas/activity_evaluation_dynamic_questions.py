import uuid

from pydantic import BaseModel, ConfigDict

from app.enums.enums import EvaluationResult


class ActivityEvaluationDynamicQuestionsBase(BaseModel):
    """
    Base schema for activity evaluation dynamic questions
    """

    evaluation_template_id: uuid.UUID
    data: str = ""
    evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    position: int = 0

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "evaluation_template_id": "00000000-0000-0000-0000-000000000000",
                "data": "Yes, all relevant information are provided.",
                "evaluation_result": "pass",
                "position": 0,
            }
        },
    )


class ActivityEvaluationDynamicQuestionsRead(ActivityEvaluationDynamicQuestionsBase):
    """
    Read schema for activity evaluation dynamic questions
    """

    id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                **ActivityEvaluationDynamicQuestionsBase.model_config.get(
                    "json_schema_extra", {}
                ).get("example", {}),
                "id": "00000000-0000-0000-0000-000000000000",
            }
        },
    )


class ActivityEvaluationDynamicQuestionsUpdate(BaseModel):
    """
    Update schema for activity evaluation dynamic questions
    """

    evaluation_template_id: uuid.UUID
    data: str | None = None
    evaluation_result: EvaluationResult | None = None


class DynamicEvaluationQuestionAssign(BaseModel):
    """
    Schema for assigning dynamic questions
    """

    evaluation_template_id: uuid.UUID
    position: int = 0
