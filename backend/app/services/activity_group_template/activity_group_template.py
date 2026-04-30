from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.activity_group_template import ActivityGroupTemplate
from app.models.user import User
from app.schemas.activity_group_template import ActivityGroupTemplateFilter
from app.schemas.general import PaginatedResponse
from app.services.utils.query import paginated_query


def get_all_activity_template_groups_service(
    user: User,
    session: Session,
    filter_query: ActivityGroupTemplateFilter,
) -> PaginatedResponse[ActivityGroupTemplate]:
    """
    Get all activity template groups.
    """
    base_statement = select(ActivityGroupTemplate).options(
        selectinload(ActivityGroupTemplate.activity_templates)
    )
    return paginated_query(
        session, ActivityGroupTemplate, filter_query, base_statement=base_statement
    )
