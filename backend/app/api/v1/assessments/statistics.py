import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.statistics import AssessmentStatisticsResponse
from app.services.statistics.assessment_statistics import (
    get_assessment_statistics_service,
)

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
)


@router.get("/", response_model=AssessmentStatisticsResponse)
def get_assessment_statistics_endpoint(
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
) -> AssessmentStatisticsResponse:
    """
    Get statistics for a single assessment.

    Returns metrics over visible, non-deleted activities in visible,
    non-deleted groups. All roles see the same data.
    """
    return get_assessment_statistics_service(assessment_id, session)
