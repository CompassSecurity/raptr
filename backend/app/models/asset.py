import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base, SoftDeleteMixin


class Asset(SoftDeleteMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(255), nullable=True)
    # Complicated mapping because SQLite test db does not support JSONB
    properties: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=dict
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment.id", ondelete="CASCADE")
    )
