import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.enums import UserRole
from app.models.acl import Acl
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.activity_evaluation_dynamic_questions import (
    DynamicEvaluationQuestionAssign,
)
from app.schemas.assessment import AssessmentBase, AssessmentFilter
from app.schemas.general import PaginatedResponse
from app.services.activity_group.activity_group import get_or_create_default_group
from app.services.utils.query import paginated_query


def get_all_assessments_service(
    user: User,
    session: Session,
    filter_query: AssessmentFilter,
) -> PaginatedResponse[Assessment]:
    """
    Get all assessments. Searchable by assessment name. For 'user' role results are filtered by ACL.
    Returns a PaginatedResponse with assessments and pagination metadata.
    """
    base_statement = select(Assessment)
    if user.role != UserRole.ADMIN:
        base_statement = base_statement.join(Acl).where(Acl.user_id == user.id)

    return paginated_query(
        session, Assessment, filter_query, base_statement=base_statement
    )


def get_assessment_by_id_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Assessment:
    """
    Get an assessment by ID. For 'user' role, results are filtered by ACL.
    """
    statement = select(Assessment).where(Assessment.id == assessment_id)
    if user.role != UserRole.ADMIN:
        statement = statement.join(Acl).where(Acl.user_id == user.id)
    assessment = session.execute(statement).scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )
    return assessment


def create_assessment_service(
    assessment: AssessmentBase,
    user: User,
    session: Session,
) -> Assessment:
    """
    Create a new assessment.
    """
    db_assessment = Assessment(
        name=assessment.name,
        description=assessment.description,
        assessment_type=assessment.assessment_type,
        created_by=user.id,
    )
    session.add(db_assessment)
    session.flush()
    get_or_create_default_group(db_assessment.id, session, created_by=user.id)
    session.commit()
    return db_assessment


def delete_assessment_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Delete an assessment by ID.
    """
    db_assessment = get_assessment_by_id_service(assessment_id, user, session)
    session.delete(db_assessment)
    session.commit()


def update_assessment_service(
    assessment_id: uuid.UUID,
    assessment: AssessmentBase,
    user: User,
    session: Session,
) -> Assessment:
    """
    Update an assessment by ID.
    """
    db_assessment = get_assessment_by_id_service(assessment_id, user, session)
    db_assessment.name = assessment.name
    db_assessment.description = assessment.description
    db_assessment.assessment_type = assessment.assessment_type
    db_assessment.updated_by = user.id
    session.commit()
    return db_assessment


def update_assessment_evaluation_template_service(
    assessment_id: uuid.UUID,
    dynamic_evaluation_questions: list[DynamicEvaluationQuestionAssign],
    user: User,
    session: Session,
) -> Assessment:
    """
    Update an assessment's default evaluation templates.
    """
    db_assessment = get_assessment_by_id_service(assessment_id, user, session)
    templates = []
    for question in dynamic_evaluation_questions:
        template_entry = {
            "evaluation_template_id": str(question.evaluation_template_id),
            "position": question.position,
        }
        templates.append(template_entry)

    db_assessment.default_evaluation_templates = templates
    db_assessment.updated_by = user.id
    session.commit()
    return db_assessment
