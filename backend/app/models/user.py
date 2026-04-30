import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.enums.enums import UserRole
from app.models.base import Base


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    mfa_verified: Mapped[bool] = mapped_column(default=False)
    mfa_secret: Mapped[str | None] = mapped_column(default=None)
    hashed_password: Mapped[str | None] = mapped_column(default=None)
    disabled: Mapped[bool] = mapped_column(default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_logout_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
