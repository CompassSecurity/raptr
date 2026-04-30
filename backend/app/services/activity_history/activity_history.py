import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.activity import Activity
from app.models.activity_history import ActivityHistory
from app.models.user import User
from app.schemas.activity import ActivityRead


def save_activity_shadow_copy(
    activity_db: Activity, session: Session
) -> ActivityHistory:
    """
    Creates a shadow copy (version snapshot) of the given activity.
    The snapshot contains the full serialized state of the activity.
    """
    # Use ActivityRead Pydantic schema to correctly serialize all the relationships without the files.
    # We must ensure all relations are loaded before doing this. They should be, given how `Activity` is set up.

    # We temporarily avoid Pydantic serialization loops/issues by directly dumping
    # Flush instead of refresh so that uncommitted changes are pushed to DB but we don't overwrite local object state
    session.flush()
    snapshot_data = ActivityRead.model_validate(activity_db).model_dump(mode="json")

    # We calculate the next version number for this activity
    current_max_version = session.scalar(
        select(func.max(ActivityHistory.version)).where(
            ActivityHistory.activity_id == activity_db.id
        )
    )
    next_version = (current_max_version or 0) + 1

    history_entry = ActivityHistory(
        activity_id=activity_db.id,
        version=next_version,
        saved_at=func.now(),
        saved_by_id=activity_db.updated_by or activity_db.created_by,
        snapshot=snapshot_data,
    )

    session.add(history_entry)
    session.flush()

    return history_entry


def get_activity_history_list_service(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Sequence[ActivityHistory]:
    """
    Retrieve all history versions for a given activity.
    """
    from app.services.activity.activity import get_activity_by_id_service

    # First ensure the user has access to this activity and it belongs to the assessment
    get_activity_by_id_service(activity_id, assessment_id, user, session)

    stmt = (
        select(ActivityHistory)
        .where(ActivityHistory.activity_id == activity_id)
        .order_by(ActivityHistory.version.desc())
    )
    return session.execute(stmt).scalars().all()


def get_activity_history_version_service(
    activity_id: uuid.UUID,
    version_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityHistory:
    """
    Retrieve a specific history version for a given activity.
    """
    from app.services.activity.activity import get_activity_by_id_service

    # Ensure access
    get_activity_by_id_service(activity_id, assessment_id, user, session)

    stmt = select(ActivityHistory).where(
        ActivityHistory.activity_id == activity_id,
        ActivityHistory.id == version_id,
    )
    history_entry = session.scalar(stmt)

    if not history_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity history version not found",
        )

    return history_entry
