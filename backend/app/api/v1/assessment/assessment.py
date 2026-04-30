import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.authorization import (
    admin_role_validation_service,
    require_assessment_role,
)
from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.activity_evaluation_dynamic_questions import (
    DynamicEvaluationQuestionAssign,
)
from app.schemas.assessment import AssessmentBase, AssessmentFilter, AssessmentRead
from app.schemas.assessment_export import ImportResponse
from app.schemas.general import MessageResponse, PaginatedResponse
from app.services.assessment.assessment import (
    create_assessment_service,
    delete_assessment_service,
    get_all_assessments_service,
    get_assessment_by_id_service,
    update_assessment_evaluation_template_service,
    update_assessment_service,
)
from app.services.assessment.assessment_import import import_assessment_service

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/", response_model=PaginatedResponse[AssessmentRead])
def get_assessments(
    filter_query: Annotated[AssessmentFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all assessments.
    """
    assessments = get_all_assessments_service(user, session, filter_query)
    return assessments


@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get an assessment by ID.
    """
    assessment = get_assessment_by_id_service(assessment_id, user, session)
    return assessment


@router.post("/", response_model=AssessmentRead)
def create_assessment(
    assessment: AssessmentBase,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Create a new assessment.
    """
    assessment = create_assessment_service(assessment, user, session)
    return assessment


@router.post("/import", response_model=ImportResponse)
def import_assessment(
    file: UploadFile = File(...),
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Import an assessment from an exported zip archive.
    Creates a new assessment with all child data.
    """
    zip_bytes = file.file.read()
    return import_assessment_service(zip_bytes, user, session)


@router.put("/{assessment_id}", response_model=AssessmentRead)
def update_assessment(
    assessment: AssessmentBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Update an assessment by ID.
    """
    assessment = update_assessment_service(assessment_id, assessment, user, session)
    return assessment


@router.delete("/{assessment_id}", response_model=MessageResponse)
def delete_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Delete an assessment by ID.
    """
    delete_assessment_service(assessment_id, user, session)
    return MessageResponse(message="Assessment deleted successfully")


@router.put(
    "/{assessment_id}/default_evaluation_templates", response_model=AssessmentRead
)
def update_assessment_default_evaluation_templates(
    assessment_id: uuid.UUID,
    dynamic_evaluation_questions: list[DynamicEvaluationQuestionAssign],
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Update an assessment's evaluation template.
    """
    assessment = update_assessment_evaluation_template_service(
        assessment_id, dynamic_evaluation_questions, user, session
    )
    return assessment
