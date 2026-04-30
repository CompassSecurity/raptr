import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.activity_template import ActivityTemplateFilter, ActivityTemplateRead
from app.schemas.general import PaginatedResponse
from app.services.activity_template.activity_template import (
    get_activity_template_by_id_service,
    get_all_activity_templates_service,
)

router = APIRouter(
    prefix="/activity_template",
    tags=["activity_template"],
)


@router.get("/", response_model=PaginatedResponse[ActivityTemplateRead])
def get_activity_templates(
    filter_query: Annotated[ActivityTemplateFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all activity templates.
    """
    return get_all_activity_templates_service(user, session, filter_query)


@router.get("/{activity_template_id}", response_model=ActivityTemplateRead)
def get_activity_template(
    activity_template_id: uuid.UUID,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get an activity template by ID.
    """
    return get_activity_template_by_id_service(activity_template_id, user, session)
