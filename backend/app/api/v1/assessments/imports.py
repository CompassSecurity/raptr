import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.general import MessageResponse
from app.services.imports.imports import (
    import_from_activity_group_templates_service,
    import_from_activity_templates_service,
    import_from_campaign_template_service,
)

router = APIRouter(
    prefix="/imports",
    tags=["imports"],
)


@router.post("/activity_templates", response_model=MessageResponse)
def import_from_activity_templates(
    activity_template_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Import multiple activities from activity templates.
    """
    count = import_from_activity_templates_service(
        activity_template_ids, assessment_id, user, session
    )
    return MessageResponse(message=f"{count} activities imported successfully")


@router.post("/activity_group_templates", response_model=MessageResponse)
def import_from_activity_group_templates(
    activity_group_template_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Import multiple activity groups from activity group templates.
    """
    count = import_from_activity_group_templates_service(
        activity_group_template_ids, assessment_id, user, session
    )
    return MessageResponse(
        message=f"{count} activity groups and their activities imported successfully."
    )


@router.post("/campaign_template", response_model=MessageResponse)
def import_from_campaign_template(
    campaign_template_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Import all content from a campaign template into an assessment.
    Creates groups and activities with correct ordering.
    """
    msg = import_from_campaign_template_service(
        campaign_template_id, assessment_id, user, session
    )
    return MessageResponse(message=msg)
