import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.enums.enums import EvaluationResult
from app.models.activity import Activity
from app.models.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestions,
)
from app.models.base import Base


class ActivityEvaluation(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("activity.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    activity: Mapped["Activity"] = relationship("Activity", back_populates="evaluation")

    # General evaluation
    logged_evaluation: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )
    alerted_evaluation: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )
    prevented_evaluation: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )
    stakeholder_notified_evaluation: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )

    # Activity coverage score
    activity_coverage_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Time-based evaluation
    event_to_alert_data: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    event_to_alert_evaluation_result: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )

    alert_to_stakeholder_data: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    alert_to_stakeholder_evaluation_result: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )

    # Severity-based evaluation
    alert_severity_data: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    alert_severity_evaluation_result: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )

    stakeholder_notification_severity_data: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    stakeholder_notification_severity_evaluation_result: Mapped[EvaluationResult] = (
        mapped_column(
            Enum(EvaluationResult),
            nullable=False,
            default=EvaluationResult.NOT_APPLICABLE,
        )
    )

    dynamic_questions: Mapped[list["ActivityEvaluationDynamicQuestions"]] = (
        relationship(
            "ActivityEvaluationDynamicQuestions",
            back_populates="activity_evaluation",
            cascade="all, delete-orphan",
            lazy="selectin",
            order_by="ActivityEvaluationDynamicQuestions.position",
        )
    )
