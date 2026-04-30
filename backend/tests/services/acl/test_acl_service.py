import uuid

import pytest
from fastapi import HTTPException

from app.models.assessment import Assessment
from app.schemas.acl import AclBase
from app.services.acl.acl import (
    create_acl_service,
    delete_acl_service,
    get_acl_by_id_service,
    update_acl_service,
)


@pytest.fixture
def assessment(session, test_admin_user):
    assessment = Assessment(
        name="ACL Service Test",
        description="Desc",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def test_create_acl_service_success(
    session, assessment, test_regular_user, test_admin_user
):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    acl = create_acl_service(acl_data, test_admin_user, session)
    assert acl.user_id == test_regular_user.id
    assert acl.assessment_id == assessment.id
    assert acl.assessment_role == "spectator"


def test_create_acl_service_admin_target_fail(session, assessment, test_admin_user):
    # Try to create ACL for the admin user itself
    acl_data = AclBase(
        user_id=test_admin_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 400
    assert "Admins do not require ACLs" in exc.value.detail


def test_create_acl_service_user_not_found(session, assessment, test_admin_user):
    acl_data = AclBase(
        user_id=uuid.uuid4(), assessment_id=assessment.id, assessment_role="spectator"
    )
    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 404
    assert "User not found" in exc.value.detail


def test_create_acl_service_assessment_not_found(
    session, test_regular_user, test_admin_user
):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=uuid.uuid4(),
        assessment_role="spectator",
    )
    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 404
    assert "Assessment not found" in exc.value.detail


def test_create_acl_service_duplicate(
    session, assessment, test_regular_user, test_admin_user
):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    create_acl_service(acl_data, test_admin_user, session)

    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 400
    assert "Acl already exists" in exc.value.detail


def test_update_acl_service(session, assessment, test_regular_user, test_admin_user):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    created_acl = create_acl_service(acl_data, test_admin_user, session)

    update_data = AclBase(
        user_id=test_regular_user.id, assessment_id=assessment.id, assessment_role="red"
    )
    updated_acl = update_acl_service(
        created_acl.id, update_data, test_admin_user, session
    )
    assert updated_acl.assessment_role == "red"


def test_delete_acl_service(session, assessment, test_regular_user, test_admin_user):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    created_acl = create_acl_service(acl_data, test_admin_user, session)

    delete_acl_service(created_acl.id, test_admin_user, session)

    # Verify it's gone
    with pytest.raises(HTTPException) as exc:
        get_acl_by_id_service(created_acl.id, test_admin_user, session)
    assert exc.value.status_code == 404


def test_get_all_acls_by_assessment_service(
    session, assessment, test_regular_user, test_admin_user
):
    """
    Test retrieving all ACLs for a specific assessment.
    """
    from app.services.acl.acl import get_all_acls_by_assessment_service

    # Create ACLs for the assessment
    acl_data1 = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    create_acl_service(acl_data1, test_admin_user, session)

    # Fetch ACLs by assessment ID
    acls = get_all_acls_by_assessment_service(assessment.id, test_admin_user, session)

    assert len(acls) == 1
    assert acls[0].assessment_id == assessment.id
    assert acls[0].user_id == test_regular_user.id


def test_get_all_acls_by_user_service(
    session, assessment, test_regular_user, test_admin_user
):
    """
    Test retrieving all ACLs for a specific user.
    """
    from app.services.acl.acl import get_all_acls_by_user_service

    # Create ACLs for the user
    acl_data1 = AclBase(
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        assessment_role="spectator",
    )
    create_acl_service(acl_data1, test_admin_user, session)

    # Fetch ACLs by user ID
    acls = get_all_acls_by_user_service(test_regular_user.id, test_admin_user, session)

    assert len(acls) == 1
    assert acls[0].user_id == test_regular_user.id
    assert acls[0].assessment_id == assessment.id
