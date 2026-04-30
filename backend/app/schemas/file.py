import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.enums.enums import FileCategory, FileType


class FileBase(BaseModel):
    """
    Base model for file uploads
    """

    filename: str
    content_type: FileType
    size: int
    category: FileCategory
    activity_id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "example.txt",
                "content_type": "text/plain",
                "size": 1024,
                "category": "red",
                "activity_id": "00000000-0000-0000-0000-000000000000",
            }
        },
    )


class FileRead(FileBase):
    """
    Model for reading file information
    """

    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
                "created_at": "2022-01-01T00:00:00.000Z",
                "created_by": "00000000-0000-0000-0000-000000000000",
            }
        },
    )


class FileFilter(BaseModel):
    """
    Filter schema for file queries. All fields optional.
    Inherits from BaseModel because it is not paginated.
    """

    filename: str | None = None
    category: FileCategory | None = None
    sort_by: Literal["filename", "created_at"] | None = None


class FileUploadResponse(BaseModel):
    """
    Response model for file uploads.
    """

    message: str
    url: str
    file_id: uuid.UUID
