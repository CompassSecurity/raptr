import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.activity import Activity
from app.models.base import Base, SoftDeleteMixin


class Tag(SoftDeleteMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessment.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    # Import activity_tag_association at runtime to avoid circular import
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        secondary="activity_tag",
        lazy="joined",
        back_populates="tags",
    )
