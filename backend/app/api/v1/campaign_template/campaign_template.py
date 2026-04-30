import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.campaign_template import (
    CampaignTemplateFilter,
    CampaignTemplateRead,
)
from app.schemas.general import PaginatedResponse
from app.services.campaign_template.campaign_template import (
    get_all_campaign_templates_service,
    get_campaign_template_by_id_service,
)

router = APIRouter(
    prefix="/campaign_template",
    tags=["campaign_template"],
)


@router.get("/", response_model=PaginatedResponse[CampaignTemplateRead])
def get_campaign_templates(
    filter_query: Annotated[CampaignTemplateFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all campaign templates.
    """
    return get_all_campaign_templates_service(user, session, filter_query)


@router.get("/{campaign_template_id}", response_model=CampaignTemplateRead)
def get_campaign_template(
    campaign_template_id: uuid.UUID,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get a single campaign template by ID.
    """
    return get_campaign_template_by_id_service(campaign_template_id, user, session)
