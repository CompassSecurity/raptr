import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func


class SoftDeleteMixin:
    """Mixin for models that support soft deletion."""

    @declared_attr
    def deleted(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=False)

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def deleted_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(
            Uuid,
            ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        )


class Base(DeclarativeBase):
    id: Any
    __name__: str

    # Predictable constraint names (instead of database-generated or missing ones),
    # so migrations can reference constraints the same way on PostgreSQL and SQLite
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common audit fields
    @declared_attr
    def created_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(
            Uuid,
            ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), server_default=func.now())

    @declared_attr
    def updated_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(
            Uuid,
            ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
