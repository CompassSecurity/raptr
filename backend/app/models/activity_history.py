import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base


class ActivityHistory(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("activity.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    saved_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    snapshot: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    activity = relationship("Activity", backref="history")
    saved_by = relationship("User", foreign_keys=[saved_by_id])
