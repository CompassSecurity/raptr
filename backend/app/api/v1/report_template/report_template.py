from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.report import (
    ReportTemplateFilter,
    ReportTemplateRead,
)
from app.services.report_template.report_template import (
    get_all_report_templates_service,
)

router = APIRouter(
    prefix="/report_template",
    tags=["report_template"],
)


@router.get("/", response_model=list[ReportTemplateRead])
def get_report_templates(
    filter_query: Annotated[ReportTemplateFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all report templates.
    """
    return get_all_report_templates_service(user, session, filter_query)
