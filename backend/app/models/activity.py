import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Table,
    Text,
    and_,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.enums.enums import (
    ActivityPriority,
    ActivitySeverity,
    ActivityState,
)
from app.models.asset import Asset
from app.models.base import Base, SoftDeleteMixin

# Association table for Many-to-Many relationship between Activity and Tag
activity_tag_association = Table(
    "activity_tag",
    Base.metadata,
    Column(
        "activity_id",
        Uuid,
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Uuid,
        ForeignKey("tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Association table for Many-to-Many relationship between Activity and Asset
activity_asset_association = Table(
    "activity_asset",
    Base.metadata,
    Column(
        "activity_id",
        Uuid,
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "asset_id",
        Uuid,
        ForeignKey("asset.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role",
        String(50),
        primary_key=True,
    ),
)


class Activity(SoftDeleteMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mitre_tactic: Mapped[str] = mapped_column(String(255), nullable=False)
    mitre_technique: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=True)
    priority: Mapped[ActivityPriority] = mapped_column(
        Enum(ActivityPriority), nullable=True
    )
    visible: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    activity_position: Mapped[int] = mapped_column(default=0)
    state: Mapped[ActivityState] = mapped_column(
        Enum(ActivityState), nullable=True, default=ActivityState.PENDING
    )
    linked_knowledge_base_articles: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Activity fields
    activity_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    activity_actions: Mapped[str] = mapped_column(Text, nullable=True)
    activity_requirements: Mapped[str] = mapped_column(Text, nullable=True)
    activity_notes: Mapped[str] = mapped_column(Text, nullable=True)
    activity_start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activity_end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Expected results
    expected_logging: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_prevention: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_alert_creation: Mapped[bool] = mapped_column(Boolean, nullable=True)
    expected_stakeholder_notification: Mapped[bool] = mapped_column(
        Boolean, nullable=True
    )
    expected_severity: Mapped[ActivitySeverity] = mapped_column(
        Enum(ActivitySeverity), nullable=True
    )

    # Results
    logged: Mapped[bool] = mapped_column(Boolean, nullable=True)
    log_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    prevented: Mapped[bool] = mapped_column(Boolean, nullable=True)
    prevent_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    alerted: Mapped[bool] = mapped_column(Boolean, nullable=True)
    alert_severity: Mapped[str] = mapped_column(String(255), nullable=True)
    alert_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stakeholder_notification_created: Mapped[bool] = mapped_column(
        Boolean, nullable=True
    )
    stakeholder_notification_severity: Mapped[str] = mapped_column(
        String(255), nullable=True
    )
    stakeholder_notification_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Detection notes
    log_notes: Mapped[str] = mapped_column(Text, nullable=True)
    alert_notes: Mapped[str] = mapped_column(Text, nullable=True)
    prevent_notes: Mapped[str] = mapped_column(Text, nullable=True)
    stakeholder_notification_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Activity Group
    activity_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("activitygroup.id"), nullable=True
    )

    # Relationships
    activity_group = relationship(
        "ActivityGroup", back_populates="activities", lazy="joined"
    )
    tags = relationship(
        "Tag",
        secondary=activity_tag_association,
        lazy="joined",
        back_populates="activities",
    )

    # Asset relationships filtered by role
    sources = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "source",
        ),
        lazy="selectin",
        viewonly=True,
    )
    targets = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "target",
        ),
        lazy="selectin",
        viewonly=True,
    )
    tools = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "tool",
        ),
        lazy="selectin",
        viewonly=True,
    )
    log_sources = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "log_source",
        ),
        lazy="selectin",
        viewonly=True,
    )
    prevention_sources = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "prevention_source",
        ),
        lazy="selectin",
        viewonly=True,
    )
    alert_sources = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "alert_source",
        ),
        lazy="selectin",
        viewonly=True,
    )
    stakeholder_notification_sources = relationship(
        "Asset",
        secondary=activity_asset_association,
        primaryjoin=lambda: Activity.id == activity_asset_association.c.activity_id,
        secondaryjoin=lambda: and_(
            Asset.id == activity_asset_association.c.asset_id,
            activity_asset_association.c.role == "stakeholder_notification_source",
        ),
        lazy="selectin",
        viewonly=True,
    )

    evaluation = relationship(
        "ActivityEvaluation",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    files = relationship(
        "File",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
