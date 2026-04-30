import uuid

from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.enums.enums import AssessmentType
from app.models.base import Base


class Assessment(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    assessment_type: Mapped[AssessmentType] = mapped_column(Enum(AssessmentType))
    default_evaluation_templates: Mapped[list[dict[str, str | int]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
