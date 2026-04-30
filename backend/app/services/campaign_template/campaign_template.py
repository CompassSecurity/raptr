import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.campaign_template import CampaignTemplate
from app.models.user import User
from app.schemas.campaign_template import CampaignTemplateFilter
from app.schemas.general import PaginatedResponse
from app.services.utils.query import paginated_query


def get_all_campaign_templates_service(
    user: User,
    session: Session,
    filter_query: CampaignTemplateFilter,
) -> PaginatedResponse[CampaignTemplate]:
    """
    Get all campaign templates with their items.
    """
    base_statement = select(CampaignTemplate).options(
        selectinload(CampaignTemplate.items)
    )
    return paginated_query(
        session, CampaignTemplate, filter_query, base_statement=base_statement
    )


def get_campaign_template_by_id_service(
    campaign_template_id: uuid.UUID,
    user: User,
    session: Session,
) -> CampaignTemplate:
    """
    Get a single campaign template by ID.
    """
    statement = (
        select(CampaignTemplate)
        .options(selectinload(CampaignTemplate.items))
        .where(CampaignTemplate.id == campaign_template_id)
    )
    campaign_template = session.execute(statement).scalar_one_or_none()
    if not campaign_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign template not found"
        )
    return campaign_template
