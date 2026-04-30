import uuid

from sqlalchemy import Enum, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.enums.enums import ReportTemplateFormat
from app.models.base import Base


class ReportTemplate(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ReportTemplateFormat] = mapped_column(
        Enum(ReportTemplateFormat), nullable=False
    )
    template_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
