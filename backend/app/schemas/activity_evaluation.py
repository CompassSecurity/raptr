import uuid

from pydantic import BaseModel, ConfigDict

from app.enums.enums import EvaluationResult
from app.schemas.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestionsBase,
    ActivityEvaluationDynamicQuestionsRead,
    ActivityEvaluationDynamicQuestionsUpdate,
)


class ActivityEvaluationBase(BaseModel):
    """
    Activity Evaluation base schema
    """

    logged_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    alerted_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    prevented_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    stakeholder_notified_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    activity_coverage_score: int = 0

    # Time-based evaluation
    event_to_alert_data: str = ""
    event_to_alert_evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE

    alert_to_stakeholder_data: str = ""
    alert_to_stakeholder_evaluation_result: EvaluationResult = (
        EvaluationResult.NOT_APPLICABLE
    )

    # Severity-based evaluation
    alert_severity_data: str = ""
    alert_severity_evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE

    stakeholder_notification_severity_data: str = ""
    stakeholder_notification_severity_evaluation_result: EvaluationResult = (
        EvaluationResult.NOT_APPLICABLE
    )

    dynamic_questions: list[ActivityEvaluationDynamicQuestionsBase] = []


class ActivityEvaluationRead(ActivityEvaluationBase):
    """
    Activity Evaluation read schema
    """

    id: uuid.UUID
    activity_id: uuid.UUID
    dynamic_questions: list[ActivityEvaluationDynamicQuestionsRead] = []

    model_config = ConfigDict(from_attributes=True)


class ActivityEvaluationUpdate(ActivityEvaluationBase):
    """
    Activity Evaluation update schema
    """

    dynamic_questions: list[ActivityEvaluationDynamicQuestionsUpdate] | None = None
