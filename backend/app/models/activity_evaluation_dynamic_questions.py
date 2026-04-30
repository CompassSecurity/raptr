import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.enums.enums import EvaluationResult
from app.models.base import Base


class ActivityEvaluationDynamicQuestions(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )

    activity_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("activityevaluation.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluationtemplate.id", ondelete="CASCADE"),
        nullable=False,
    )

    data: Mapped[str] = mapped_column(String, nullable=False, default="")
    evaluation_result: Mapped[EvaluationResult] = mapped_column(
        Enum(EvaluationResult), nullable=False, default=EvaluationResult.NOT_APPLICABLE
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    activity_evaluation = relationship(
        "ActivityEvaluation", back_populates="dynamic_questions"
    )
    evaluation_template = relationship("EvaluationTemplate")

    # Constraint to ensure only one dynamic question per evaluation template per activity
    __table_args__ = (
        UniqueConstraint(
            "activity_evaluation_id",
            "evaluation_template_id",
            name="uq_activity_evaluation_template",
        ),
    )
