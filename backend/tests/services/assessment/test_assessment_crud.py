import uuid

import pytest
from fastapi import HTTPException

from app.schemas.assessment import AssessmentBase, AssessmentFilter
from app.services.assessment.assessment import (
    create_assessment_service,
    delete_assessment_service,
    get_all_assessments_service,
    get_assessment_by_id_service,
    update_assessment_service,
)


def test_create_assessment(session, test_admin_user):
    assessment_data = AssessmentBase(
        name="New Assessment",
        description="Test Description",
        assessment_type="PurpleTeam",
    )
    assessment = create_assessment_service(assessment_data, test_admin_user, session)

    assert assessment.name == "New Assessment"
    assert assessment.description == "Test Description"
    assert assessment.assessment_type == "PurpleTeam"
    assert assessment.created_by == test_admin_user.id


def test_get_all_assessments(session, test_admin_user):
    # Create assessments
    a1 = AssessmentBase(
        name="Assessment 1", description="D1", assessment_type="PurpleTeam"
    )
    a2 = AssessmentBase(
        name="Assessment 2", description="D2", assessment_type="RedTeam"
    )

    create_assessment_service(a1, test_admin_user, session)
    create_assessment_service(a2, test_admin_user, session)

    results = get_all_assessments_service(test_admin_user, session, AssessmentFilter())
    assert results.total >= 2


def test_get_all_assessments_with_filter(session, test_admin_user):
    a1 = AssessmentBase(
        name="Alpha Test", description="D1", assessment_type="PurpleTeam"
    )
    a2 = AssessmentBase(name="Beta Test", description="D2", assessment_type="RedTeam")

    create_assessment_service(a1, test_admin_user, session)
    create_assessment_service(a2, test_admin_user, session)

    results = get_all_assessments_service(
        test_admin_user, session, AssessmentFilter(name="Alpha")
    )
    assert results.total == 1
    assert results.items[0].name == "Alpha Test"


def test_get_assessment_by_id(session, test_admin_user):
    assessment_data = AssessmentBase(
        name="Test Assessment", description="Description", assessment_type="PurpleTeam"
    )
    created = create_assessment_service(assessment_data, test_admin_user, session)

    fetched = get_assessment_by_id_service(created.id, test_admin_user, session)
    assert fetched.id == created.id
    assert fetched.name == "Test Assessment"


def test_get_assessment_by_id_not_found(session, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        get_assessment_by_id_service(uuid.uuid4(), test_admin_user, session)
    assert exc.value.status_code == 404


def test_update_assessment(session, test_admin_user):
    assessment_data = AssessmentBase(
        name="Original", description="Original Desc", assessment_type="PurpleTeam"
    )
    created = create_assessment_service(assessment_data, test_admin_user, session)

    update_data = AssessmentBase(
        name="Updated", description="Updated Desc", assessment_type="RedTeam"
    )
    updated = update_assessment_service(
        created.id, update_data, test_admin_user, session
    )

    assert updated.name == "Updated"
    assert updated.description == "Updated Desc"
    assert updated.assessment_type == "RedTeam"


def test_update_assessment_not_found(session, test_admin_user):
    update_data = AssessmentBase(
        name="X", description="X", assessment_type="PurpleTeam"
    )
    with pytest.raises(HTTPException) as exc:
        update_assessment_service(uuid.uuid4(), update_data, test_admin_user, session)
    assert exc.value.status_code == 404


def test_delete_assessment(session, test_admin_user):
    assessment_data = AssessmentBase(
        name="To Delete", description="Description", assessment_type="PurpleTeam"
    )
    created = create_assessment_service(assessment_data, test_admin_user, session)

    result = delete_assessment_service(created.id, test_admin_user, session)
    assert result is None

    # Verify deletion
    with pytest.raises(HTTPException) as exc:
        get_assessment_by_id_service(created.id, test_admin_user, session)
    assert exc.value.status_code == 404


def test_delete_assessment_not_found(session, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        delete_assessment_service(uuid.uuid4(), test_admin_user, session)
    assert exc.value.status_code == 404
