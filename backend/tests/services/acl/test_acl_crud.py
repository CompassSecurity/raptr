import uuid

import pytest
from fastapi import HTTPException

from app.enums.enums import AclRole
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.acl import AclBase
from app.services.acl.acl import (
    create_acl_service,
    delete_acl_service,
    get_acl_by_id_service,
    get_all_acls_by_user_service,
    update_acl_service,
)


@pytest.fixture
def test_assessment(session, test_admin_user):
    assessment = Assessment(
        name="Test Assessment",
        description="Description",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


@pytest.fixture
def test_regular_user(session, test_admin_user):
    user = User(
        email="regular@test.com",
        role="user",
        disabled=False,
        hashed_password="hashed",
        created_by=test_admin_user.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_create_acl(session, test_assessment, test_admin_user, test_regular_user):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )
    acl = create_acl_service(acl_data, test_admin_user, session)

    assert acl.user_id == test_regular_user.id
    assert acl.assessment_id == test_assessment.id
    assert acl.assessment_role == AclRole.RED


def test_create_acl_duplicate_raises(
    session, test_assessment, test_admin_user, test_regular_user
):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )
    create_acl_service(acl_data, test_admin_user, session)

    # Try to create duplicate
    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


def test_create_acl_for_admin_raises(session, test_assessment, test_admin_user):
    acl_data = AclBase(
        user_id=test_admin_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )

    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 400
    assert "Admins do not require ACLs" in exc.value.detail


def test_create_acl_user_not_found(session, test_assessment, test_admin_user):
    acl_data = AclBase(
        user_id=uuid.uuid4(),
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )

    with pytest.raises(HTTPException) as exc:
        create_acl_service(acl_data, test_admin_user, session)
    assert exc.value.status_code == 404


def test_get_all_acls_by_user(
    session, test_assessment, test_admin_user, test_regular_user
):
    # Create second assessment
    assessment2 = Assessment(
        name="Assessment 2",
        description="Desc",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment2)
    session.commit()

    # Create ACLs for user on both assessments
    create_acl_service(
        AclBase(
            user_id=test_regular_user.id,
            assessment_id=test_assessment.id,
            assessment_role=AclRole.RED,
        ),
        test_admin_user,
        session,
    )
    create_acl_service(
        AclBase(
            user_id=test_regular_user.id,
            assessment_id=assessment2.id,
            assessment_role=AclRole.BLUE,
        ),
        test_admin_user,
        session,
    )

    acls = get_all_acls_by_user_service(test_regular_user.id, test_admin_user, session)
    assert len(acls) == 2


def test_update_acl(session, test_assessment, test_admin_user, test_regular_user):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )
    created = create_acl_service(acl_data, test_admin_user, session)

    update_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.BLUE,
    )
    updated = update_acl_service(created.id, update_data, test_admin_user, session)

    assert updated.assessment_role == AclRole.BLUE


def test_update_acl_not_found(
    session, test_assessment, test_admin_user, test_regular_user
):
    update_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.BLUE,
    )

    with pytest.raises(HTTPException) as exc:
        update_acl_service(uuid.uuid4(), update_data, test_admin_user, session)
    assert exc.value.status_code == 404


def test_delete_acl(session, test_assessment, test_admin_user, test_regular_user):
    acl_data = AclBase(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role=AclRole.RED,
    )
    created = create_acl_service(acl_data, test_admin_user, session)

    delete_acl_service(created.id, test_admin_user, session)

    # Verify deletion
    with pytest.raises(HTTPException) as exc:
        get_acl_by_id_service(created.id, test_admin_user, session)
    assert exc.value.status_code == 404
