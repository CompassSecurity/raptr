from sqlalchemy.orm import Session

from app.models.report_template import ReportTemplate
from app.models.user import User
from app.schemas.report import ReportTemplateFilter
from app.services.utils.query import query


def get_all_report_templates_service(
    user: User,
    session: Session,
    filter_query: ReportTemplateFilter,
) -> list[ReportTemplate]:
    """
    Get all report templates (metadata only).
    """
    return query(session, ReportTemplate, filter_query)
