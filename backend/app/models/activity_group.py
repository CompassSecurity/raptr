import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.activity import Activity
from app.models.base import Base, SoftDeleteMixin


class ActivityGroup(SoftDeleteMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessment.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    activity_group_position: Mapped[int] = mapped_column(Integer, default=0)

    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="activity_group",
        order_by="Activity.activity_position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
