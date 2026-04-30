import uuid

from sqlalchemy import Enum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.enums.enums import FileCategory, FileType
from app.models.activity import Activity
from app.models.base import Base


class File(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[FileType] = mapped_column(Enum(FileType), nullable=False)
    file_content: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[FileCategory] = mapped_column(Enum(FileCategory), nullable=False)

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("activity.id", ondelete="CASCADE"),
        nullable=False,
    )

    activity: Mapped["Activity"] = relationship("Activity", back_populates="files")
