import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.activity_template import ActivityTemplate


# Association Table with position for ordering
activity_template_activity_group = Table(
    "activity_template_activity_group",
    Base.metadata,
    Column(
        "activity_template_id",
        Uuid,
        ForeignKey("activitytemplate.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "activity_group_template_id",
        Uuid,
        ForeignKey("activitygrouptemplate.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("position", Integer, nullable=False, default=0),
)


class ActivityGroupTemplate(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    activity_templates: Mapped[list["ActivityTemplate"]] = relationship(
        "ActivityTemplate",
        secondary=activity_template_activity_group,
        back_populates="activity_groups",
        order_by=activity_template_activity_group.c.position,
    )

    @property
    def activity_template_ids(self) -> list[uuid.UUID]:
        return [t.id for t in self.activity_templates]
