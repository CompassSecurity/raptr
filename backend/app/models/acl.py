import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.enums.enums import AclRole
from app.models.base import Base


class Acl(Base):
    __table_args__ = (
        UniqueConstraint("user_id", "assessment_id", name="uq_acl_user_assessment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("user.id", ondelete="CASCADE")
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment.id", ondelete="CASCADE")
    )
    assessment_role: Mapped[AclRole] = mapped_column(Enum(AclRole))
