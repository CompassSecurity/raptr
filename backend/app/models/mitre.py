import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base

# Association table for Many-to-Many relationship between Technique and Tactic
technique_tactic_association = Table(
    "technique_tactic",
    Base.metadata,
    Column(
        "technique_id",
        Uuid,
        ForeignKey("technique.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tactic_id",
        Uuid,
        ForeignKey("tactic.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tactic(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    mitre_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship to Techniques
    techniques: Mapped[list["Technique"]] = relationship(
        secondary=technique_tactic_association, back_populates="tactics"
    )


class Technique(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    mitre_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship to Tactics
    tactics: Mapped[list["Tactic"]] = relationship(
        secondary=technique_tactic_association, back_populates="techniques"
    )
