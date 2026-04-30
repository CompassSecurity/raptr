import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.evaluation_template import (
    EvaluationTemplateFilter,
    EvaluationTemplateRead,
)
from app.schemas.general import PaginatedResponse
from app.services.evaluation_template.evaluation_template import (
    get_all_evaluation_templates_service,
    get_evaluation_template_service,
)

router = APIRouter(
    prefix="/evaluation_template",
    tags=["evaluation_template"],
)


@router.get("/", response_model=PaginatedResponse[EvaluationTemplateRead])
def get_evaluation_templates(
    filter_query: Annotated[EvaluationTemplateFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all evaluation question templates.
    """
    return get_all_evaluation_templates_service(user, session, filter_query)


@router.get("/{evaluation_template_id}", response_model=EvaluationTemplateRead)
def get_evaluation_template_by_id(
    evaluation_template_id: uuid.UUID,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get evaluation question template by id.
    """
    return get_evaluation_template_service(evaluation_template_id, user, session)
