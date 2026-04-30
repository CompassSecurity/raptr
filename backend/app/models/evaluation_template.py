import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base


class EvaluationTemplate(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    evaluation_criteria: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
