import uuid

from fastapi import HTTPException, UploadFile, status
from pathvalidate import sanitize_filename
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, undefer

from app.enums.enums import AclRole, FileCategory, FileType
from app.models.activity import Activity
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileFilter, FileUploadResponse
from app.services.activity.activity import get_activity_by_id_service
from app.services.utils.query import query


def get_activity_files_service(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: FileFilter,
) -> list[File]:
    """
    Get all files for a specific activity with filtering.
    """

    get_activity_by_id_service(activity_id, assessment_id, user, session)

    statement = (
        select(File)
        .join(Activity)
        .where(
            and_(
                Activity.id == activity_id,
                Activity.assessment_id == assessment_id,
            )
        )
    )

    return query(session, File, filter_query, base_statement=statement)


def get_activity_file_by_id_service(
    file_id: uuid.UUID,
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> File:
    """
    Get a specific file.
    """

    get_activity_by_id_service(activity_id, assessment_id, user, session)
    statement = (
        select(File)
        .join(Activity)
        .where(
            and_(
                File.id == file_id,
                Activity.id == activity_id,
                Activity.assessment_id == assessment_id,
            )
        )
        .options(undefer(File.file_content))
    )

    file = session.execute(statement).scalars().first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return file


def validate_file_content(file: UploadFile) -> FileType:
    """
    Validate file content type using magic bytes.
    Returns the detected FileType or raises HTTPException.
    """
    MAGIC_BYTES = {
        FileType.PNG: [b"\x89PNG\r\n\x1a\n"],
        FileType.JPEG: [b"\xff\xd8\xff"],
        FileType.JPG: [b"\xff\xd8\xff"],
    }

    header = file.file.read(2048)
    file.file.seek(0)

    for file_type, magic_signatures in MAGIC_BYTES.items():
        for magic in magic_signatures:
            if header.startswith(magic):
                return file_type

    # AI generated, validation is probably needed for this check.
    # If no binary match, try to validate as Text
    try:
        header.decode("utf-8")
        return FileType.TXT
    except UnicodeDecodeError:
        pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid file type or corrupted file.",
    )


def upload_file_service(
    activity_id: uuid.UUID,
    file: UploadFile,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> FileUploadResponse:
    """
    Upload a file to an activity.
    """
    get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Validate content
    detected_file_type = validate_file_content(file)
    file_content = file.file.read()

    final_filename = sanitize_filename(file.filename) or "unnamed"
    if detected_file_type == FileType.TXT and not final_filename.endswith(".txt"):
        final_filename += ".txt"

    category = (
        FileCategory.RED
        if user.assessment_acl_role == AclRole.RED
        else FileCategory.BLUE
    )

    new_file = File(
        filename=final_filename,
        content_type=detected_file_type,
        file_content=file_content,
        size=len(file_content),
        category=category,
        activity_id=activity_id,
        created_by=user.id,
    )

    session.add(new_file)
    session.commit()

    download_url = f"/api/v1/assessments/{assessment_id}/activity/{activity_id}/files/{new_file.id}/download"

    return FileUploadResponse(
        message="File uploaded successfully", url=download_url, file_id=new_file.id
    )


def delete_file_service(
    file_id: uuid.UUID,
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Delete a file for an activity.
    """
    file = get_activity_file_by_id_service(
        file_id, activity_id, assessment_id, user, session
    )

    if user.assessment_acl_role == AclRole.BLUE and file.category != FileCategory.BLUE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this file.",
        )
    session.delete(file)
    session.commit()
