import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.models.activity_group_template import activity_template_activity_group
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.activity_group_template import ActivityGroupTemplate


class ActivityTemplate(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mitre_tactic: Mapped[str] = mapped_column(String(255), nullable=False)
    mitre_technique: Mapped[str] = mapped_column(String(255), nullable=False)
    activity_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    activity_actions: Mapped[str] = mapped_column(Text, nullable=True)
    activity_requirements: Mapped[str] = mapped_column(Text, nullable=True)
    activity_notes: Mapped[str] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_logging: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_prevention: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_alert_creation: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_stakeholder_notification: Mapped[bool] = mapped_column(
        Boolean, nullable=True
    )
    expected_severity: Mapped[str] = mapped_column(String(255), nullable=True)
    priority: Mapped[str] = mapped_column(String(255), nullable=True)
    linked_knowledge_base_articles: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    activity_groups: Mapped[list["ActivityGroupTemplate"]] = relationship(
        "ActivityGroupTemplate",
        secondary=activity_template_activity_group,
        back_populates="activity_templates",
    )
