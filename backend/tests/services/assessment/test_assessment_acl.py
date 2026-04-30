import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.acl import Acl
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.assessment import AssessmentFilter
from app.services.assessment.assessment import (
    get_all_assessments_service,
    get_assessment_by_id_service,
)


def test_admin_can_see_all_assessments(session: Session, test_admin_user: User):
    # Create some assessments
    a1 = Assessment(
        name="A1",
        description="D1",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    a2 = Assessment(
        name="A2",
        description="D2",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.commit()

    results = get_all_assessments_service(
        test_admin_user, session, AssessmentFilter(offset=0, limit=100)
    )
    assert results.total >= 2
    ids = [a.id for a in results.items]
    assert a1.id in ids
    assert a2.id in ids


def test_user_can_only_see_acl_assessments(
    session: Session, test_regular_user: User, test_admin_user: User
):
    # Create assessments
    a1 = Assessment(
        name="A1",
        description="D1",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    a2 = Assessment(
        name="A2",
        description="D2",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.commit()

    # Grant access to a1 only
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=a1.id,
        assessment_role="viewer",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()

    results = get_all_assessments_service(
        test_regular_user, session, AssessmentFilter(offset=0, limit=100)
    )
    # verify we only see a1
    # Note: there might be other assessments in DB from other tests if not cleaned up,
    # but we certainly should NOT see a2.
    ids = [a.id for a in results.items]
    assert a1.id in ids
    assert a2.id not in ids


def test_user_cannot_get_assessment_by_id_without_acl(
    session: Session, test_regular_user: User, test_admin_user: User
):
    a1 = Assessment(
        name="A1",
        description="D1",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(a1)
    session.commit()

    with pytest.raises(HTTPException) as exc:
        get_assessment_by_id_service(a1.id, test_regular_user, session)
    assert exc.value.status_code == 404


def test_user_can_get_assessment_by_id_with_acl(
    session: Session, test_regular_user: User, test_admin_user: User
):
    a1 = Assessment(
        name="A1",
        description="D1",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(a1)
    session.commit()

    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=a1.id,
        assessment_role="viewer",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()

    result = get_assessment_by_id_service(a1.id, test_regular_user, session)
    assert result is not None
    assert result.id == a1.id


def test_admin_can_get_any_assessment_by_id(session: Session, test_admin_user: User):
    a1 = Assessment(
        name="A1",
        description="D1",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(a1)
    session.commit()

    result = get_assessment_by_id_service(a1.id, test_admin_user, session)
    assert result is not None
    assert result.id == a1.id
