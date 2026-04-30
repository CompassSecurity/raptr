import io
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.report import ReportContextRequest, ReportGenerateRequest
from app.services.assessment.assessment_export import export_assessment_service
from app.services.mitre.mitre_navigator import generate_mitre_navigator_layer_service
from app.services.report.report import (
    generate_report_service,
    get_report_context_service,
)

router = APIRouter(
    prefix="/export",
    tags=["export"],
)


@router.post("/report/context", response_model=dict)
def get_report_context(
    assessment_id: uuid.UUID,
    request: ReportContextRequest,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Return the report data layer as JSON.
    """
    return get_report_context_service(assessment_id, request, user, session)


@router.post("/report/generate", response_class=StreamingResponse)
def generate_report(
    assessment_id: uuid.UUID,
    request: ReportGenerateRequest,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Generate a report for the assessment using the specified template.
    Returns a file download (HTML or DOCX).
    """
    result = generate_report_service(assessment_id, request, user, session)
    return StreamingResponse(
        io.BytesIO(result.content),
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )


@router.post("/mitre", response_class=StreamingResponse)
def generate_mitre_attack_navigator_layer(
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Generate a MITRE ATT&CK Navigator layer for the assessment.
    Returns a file download (JSON).
    """
    result = generate_mitre_navigator_layer_service(assessment_id, user, session)
    return StreamingResponse(
        io.BytesIO(result.content),
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )


@router.post("/assessment", response_class=StreamingResponse)
def export_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Export the entire assessment as a zip archive download.
    """
    zip_bytes = export_assessment_service(assessment_id, user, session)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="assessment_export.zip"'},
    )
