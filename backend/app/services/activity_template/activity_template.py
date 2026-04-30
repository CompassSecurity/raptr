import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.activity_template import ActivityTemplate
from app.models.user import User
from app.schemas.activity_template import ActivityTemplateFilter, ActivityTemplateRead
from app.schemas.general import PaginatedResponse
from app.services.utils.query import paginated_query


def get_all_activity_templates_service(
    user: User,
    session: Session,
    filter_query: ActivityTemplateFilter,
) -> PaginatedResponse[ActivityTemplateRead]:
    """
    Get all activity templates.
    """
    return paginated_query(session, ActivityTemplate, filter_query)


def get_activity_template_by_id_service(
    activity_template_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityTemplate:
    """
    Get a activity template by ID.
    """
    activity_template = session.get(ActivityTemplate, activity_template_id)
    if not activity_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity template not found"
        )
    return activity_template
