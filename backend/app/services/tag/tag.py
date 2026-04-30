import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.enums import AclRole
from app.models.tag import Tag
from app.models.user import User
from app.schemas.activity import ActivityRead
from app.schemas.general import PaginatedResponse
from app.schemas.tag import TagBase, TagFilter, TagRead
from app.services.activity.activity import get_activity_by_id_service
from app.services.utils.query import paginated_query


def get_tags_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: TagFilter,
) -> PaginatedResponse[TagRead]:
    """
    Get all tags for an assessment. Searchable by name.
    """
    base_statement = select(Tag).where(
        Tag.assessment_id == assessment_id,
    )

    if user.assessment_acl_role != AclRole.RED:
        base_statement = base_statement.filter(Tag.deleted.is_(False))

    return paginated_query(session, Tag, filter_query, base_statement=base_statement)


def get_tag_by_id_service(
    tag_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> TagRead:
    """
    Get a tag by id.
    """
    statement = select(Tag).where(Tag.id == tag_id, Tag.assessment_id == assessment_id)
    tag = session.execute(statement).unique().scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    return tag


def create_tag_service(
    tag: TagBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> TagRead:
    """
    Create a new tag.
    """
    new_tag = Tag(
        name=tag.name, color=tag.color, assessment_id=assessment_id, created_by=user.id
    )
    session.add(new_tag)
    session.commit()
    return new_tag


def update_tag_service(
    tag_id: uuid.UUID,
    tag: TagBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> TagRead:
    """
    Update a tag by id.
    """
    tag_db = get_tag_by_id_service(tag_id, assessment_id, user, session)
    tag_db.name = tag.name
    tag_db.color = tag.color
    tag_db.updated_by = user.id
    session.commit()
    return tag_db


def toggle_tag_delete_service(
    tag_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Toggle the deleted flag for a tag for an assessment.
    """
    tag_db = get_tag_by_id_service(tag_id, assessment_id, user, session)

    if tag_db.deleted:
        tag_db.deleted = False
        tag_db.deleted_at = None
        tag_db.deleted_by = None
    else:
        tag_db.deleted = True
        tag_db.deleted_at = func.now()
        tag_db.deleted_by = user.id

    session.commit()


def get_tags_by_ids_service(
    tag_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> list[Tag]:
    """
    Get multiple tags by their IDs and validate they belong to the assessment.
    Raises HTTPException if any tag is not found or belongs to different assessment.
    """
    if not tag_ids:
        return []

    statement = select(Tag).where(
        Tag.id.in_(tag_ids),
        Tag.assessment_id == assessment_id,
        Tag.deleted.is_(False),
    )
    tags = session.execute(statement).scalars().unique().all()

    # Validate all tags exist
    if len(tags) != len(tag_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more tags not found or do not belong to this assessment",
        )

    return tags


def update_activity_tags_service(
    activity_id: uuid.UUID,
    tag_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityRead:
    """
    Update tags for an activity. Replaces all existing tags with the provided list.
    Validates that all tags belong to the same assessment as the activity.
    """
    # Get and validate activity exists
    activity = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Get and validate tags if provided
    if tag_ids:
        tags = get_tags_by_ids_service(tag_ids, assessment_id, user, session)
        activity.tags = tags
    else:
        # Empty list means remove all tags
        activity.tags = []

    session.commit()
    return activity
