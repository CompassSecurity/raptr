"""
Tests for generate_report_service error handling.

A sandbox-blocked (SSTI) or malformed template must surface as a clean HTTP 422
with a generic message and be logged via app_logger — never an opaque 500 or a
leaked payload.
"""

import logging

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums.enums import ReportTemplateFormat
from app.models.assessment import Assessment
from app.models.report_template import ReportTemplate
from app.models.user import User
from app.schemas.report import ReportGenerateRequest
from app.services.report.report import generate_report_service

RCE_PAYLOAD = (
    "{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}"
)


@pytest.fixture
def assessment(session: Session, test_admin_user: User) -> Assessment:
    assessment = Assessment(
        name="Test Assessment",
        description="A test assessment",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    return assessment


def _add_template(session: Session, content: str) -> ReportTemplate:
    template = ReportTemplate(
        filename="report.html",
        format=ReportTemplateFormat.HTML,
        template_content=content.encode("utf-8"),
    )
    session.add(template)
    session.commit()
    return template


def test_malicious_template_rejected_with_422_and_logged(
    session: Session,
    test_admin_user: User,
    assessment: Assessment,
    caplog,
):
    template = _add_template(session, f"<pre>{RCE_PAYLOAD}</pre>")
    request = ReportGenerateRequest(template_id=template.id)

    with caplog.at_level(logging.ERROR, logger=settings.APPLICATION_NAME):
        with pytest.raises(HTTPException) as exc_info:
            generate_report_service(assessment.id, request, test_admin_user, session)

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # Client message stays generic — no payload echoed back.
    assert "disallowed expressions" in exc_info.value.detail
    assert "os" not in exc_info.value.detail
    # Security event is logged server-side with the template identity.
    assert str(template.id) in caplog.text


def test_malformed_template_rejected_with_422(
    session: Session,
    test_admin_user: User,
    assessment: Assessment,
):
    template = _add_template(session, "<h1>{{ unclosed </h1>")
    request = ReportGenerateRequest(template_id=template.id)

    with pytest.raises(HTTPException) as exc_info:
        generate_report_service(assessment.id, request, test_admin_user, session)

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_benign_template_succeeds(
    session: Session,
    test_admin_user: User,
    assessment: Assessment,
):
    template = _add_template(session, "<h1>{{ assessment.name }}</h1>")
    request = ReportGenerateRequest(template_id=template.id)

    result = generate_report_service(assessment.id, request, test_admin_user, session)

    assert result.media_type == "text/html"
    assert b"Test Assessment" in result.content
