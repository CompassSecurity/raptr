"""
Report service — entry points for the report API.
"""

import uuid
from dataclasses import asdict
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.enums import ReportTemplateFormat
from app.models.report_template import ReportTemplate
from app.models.user import User
from app.schemas.report import (
    GeneratedReport,
    ReportContextRequest,
    ReportGenerateRequest,
)
from app.services.report.render import render_docx_report, render_html_report
from app.services.report.report_data import (
    ReportContext,
    build_report_context,
    collect_report_images,
)
from app.services.utils.memory import release_memory


def generate_report_service(
    assessment_id: uuid.UUID,
    request: ReportGenerateRequest,
    user: User,
    session: Session,
) -> GeneratedReport:
    """
    Generate a report: fetch template, build context, render, return result.
    """
    template = session.execute(
        select(ReportTemplate).where(ReportTemplate.id == request.template_id)
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found"
        )

    context = build_report_context(
        assessment_id=assessment_id,
        template_filename=template.filename,
        session=session,
        user=user,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )

    if template.format == ReportTemplateFormat.HTML:
        output = render_html_report(template.template_content, context)
        result = GeneratedReport(
            content=output.encode("utf-8"),
            media_type="text/html",
            filename=template.filename,
        )
        del context, output
        release_memory()
        return result
    elif template.format == ReportTemplateFormat.DOCX:
        # Collect image data for DOCX embedding (markdown → InlineImage)
        image_data = collect_report_images(session, assessment_id)
        output = render_docx_report(template.template_content, context, image_data)

        del context, image_data
        release_memory()

        return GeneratedReport(
            content=output,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=template.filename,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {template.format}",
        )


def get_report_context_service(
    assessment_id: uuid.UUID,
    request: ReportContextRequest,
    user: User,
    session: Session,
) -> dict:
    """
    Build and return the report data layer as a JSON-serializable dict.
    """
    context = build_report_context(
        assessment_id=assessment_id,
        template_filename="",
        session=session,
        user=user,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )
    return _serialize_context(context)


def _serialize_context(context: ReportContext) -> dict:
    """Convert ReportContext dataclass to a JSON-serializable dict."""
    data = asdict(context)
    _serialize_datetimes(data)
    return data


def _serialize_datetimes(obj):
    """Recursively convert datetime objects to ISO strings."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, datetime):
                obj[key] = value.isoformat()
            else:
                _serialize_datetimes(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, datetime):
                obj[i] = item.isoformat()
            else:
                _serialize_datetimes(item)
