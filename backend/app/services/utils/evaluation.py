import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.enums.enums import EvaluationResult
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestions,
)
from app.models.assessment import Assessment

if TYPE_CHECKING:
    from app.models.activity import Activity


def calculate_evaluations(activity: "Activity") -> None:
    """
    Recalculate the derived evaluation fields on an activity's evaluation
    based on the activity's expected/actual boolean fields.

    Mutates activity.evaluation in place — caller is responsible for flushing/committing.
    """
    evaluation = activity.evaluation
    if evaluation is None:
        return

    def _eval(expected: bool | None, actual: bool | None) -> EvaluationResult:
        if not expected:
            return EvaluationResult.NOT_APPLICABLE
        return EvaluationResult.PASS if actual else EvaluationResult.FAIL

    evaluation.logged_evaluation = _eval(activity.expected_logging, activity.logged)
    evaluation.prevented_evaluation = _eval(
        activity.expected_prevention, activity.prevented
    )
    evaluation.alerted_evaluation = _eval(
        activity.expected_alert_creation, activity.alerted
    )
    evaluation.stakeholder_notified_evaluation = _eval(
        activity.expected_stakeholder_notification,
        activity.stakeholder_notification_created,
    )

    # Coverage score: percentage of expected checks that passed
    checks = [
        (bool(activity.expected_logging), bool(activity.logged)),
        (bool(activity.expected_prevention), bool(activity.prevented)),
        (bool(activity.expected_alert_creation), bool(activity.alerted)),
        (
            bool(activity.expected_stakeholder_notification),
            bool(activity.stakeholder_notification_created),
        ),
    ]
    expected_checks = [c for c in checks if c[0]]
    if not expected_checks:
        evaluation.activity_coverage_score = 0
    else:
        passed = sum(1 for c in expected_checks if c[1])
        evaluation.activity_coverage_score = round(
            (passed / len(expected_checks)) * 100
        )


def create_activity_evaluation(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    session: Session,
) -> ActivityEvaluation:
    """
    Create an ActivityEvaluation for an activity and populate it with
    default dynamic questions from the assessment's template configuration.
    """
    evaluation = ActivityEvaluation(activity_id=activity_id)
    session.add(evaluation)
    session.flush()

    assessment = session.get(Assessment, assessment_id)
    if assessment and assessment.default_evaluation_templates:
        for template in assessment.default_evaluation_templates:
            evaluation_question = ActivityEvaluationDynamicQuestions(
                activity_evaluation_id=evaluation.id,
                evaluation_template_id=template["evaluation_template_id"],
                position=template["position"],
            )
            session.add(evaluation_question)

    return evaluation
