from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.activity_group_template import (
    ActivityGroupTemplateFilter,
    ActivityGroupTemplateRead,
)
from app.schemas.general import PaginatedResponse
from app.services.activity_group_template.activity_group_template import (
    get_all_activity_template_groups_service,
)

router = APIRouter(
    prefix="/activity_group_template",
    tags=["activity_group_template"],
)


@router.get("/", response_model=PaginatedResponse[ActivityGroupTemplateRead])
def get_activity_group_templates(
    filter_query: Annotated[ActivityGroupTemplateFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all activity group templates.
    """
    return get_all_activity_template_groups_service(user, session, filter_query)
