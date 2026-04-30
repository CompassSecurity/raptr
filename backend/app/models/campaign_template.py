import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class CampaignTemplate(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["CampaignTemplateItem"]] = relationship(
        "CampaignTemplateItem",
        back_populates="campaign_template",
        cascade="all, delete-orphan",
        order_by="CampaignTemplateItem.position",
    )


class CampaignTemplateItem(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("campaigntemplate.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Nullable FKs — one of these will be set depending on item_type
    activity_group_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("activitygrouptemplate.id", ondelete="CASCADE"),
        nullable=True,
    )
    activity_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("activitytemplate.id", ondelete="CASCADE"),
        nullable=True,
    )

    campaign_template: Mapped["CampaignTemplate"] = relationship(
        "CampaignTemplate", back_populates="items"
    )
