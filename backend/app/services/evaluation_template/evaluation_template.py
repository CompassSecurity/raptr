import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation_template import EvaluationTemplate
from app.models.user import User
from app.schemas.evaluation_template import EvaluationTemplateFilter
from app.schemas.general import PaginatedResponse
from app.services.utils.query import paginated_query


def get_all_evaluation_templates_service(
    user: User,
    session: Session,
    filter_query: EvaluationTemplateFilter,
) -> PaginatedResponse[EvaluationTemplate]:
    """
    Get all evaluation templates.
    """
    base_statement = select(EvaluationTemplate)
    return paginated_query(
        session, EvaluationTemplate, filter_query, base_statement=base_statement
    )


def get_evaluation_template_service(
    evaluation_template_id: uuid.UUID,
    user: User,
    session: Session,
) -> EvaluationTemplate:
    """
    Get evaluation template by id.
    """
    statement = select(EvaluationTemplate).where(
        EvaluationTemplate.id == evaluation_template_id
    )
    evaluation_template = session.execute(statement).scalar_one_or_none()
    if not evaluation_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation template not found",
        )

    return evaluation_template
