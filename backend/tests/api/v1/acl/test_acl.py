import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.user import User

# Test data
ACL_ROLE = "red"


@pytest.fixture
def assessment(session: Session, test_admin_user: User) -> Assessment:
    """
    Create a test assessment for ACL tests
    """
    assessment = Assessment(
        name="ACL Test Assessment",
        description="Assessment for ACL testing",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def test_create_acl(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test creating a new ACL entry (Admin only)
    """
    response = client.post(
        "/api/v1/acl/",
        headers=auth_headers_admin,
        json={
            "assessment_role": ACL_ROLE,
            "user_id": str(test_regular_user.id),
            "assessment_id": str(assessment.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_role"] == ACL_ROLE
    assert data["user_id"] == str(test_regular_user.id)
    assert data["assessment_id"] == str(assessment.id)
    assert "id" in data


def test_create_acl_regular_user(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test that a regular user cannot create an ACL entry
    """
    response = client.post(
        "/api/v1/acl/",
        headers=auth_headers_regular,
        json={
            "assessment_role": ACL_ROLE,
            "user_id": str(test_regular_user.id),
            "assessment_id": str(assessment.id),
        },
    )
    assert response.status_code == 403


def test_get_acls(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test retrieving all ACLs (Admin only)
    """
    from app.models.acl import Acl

    new_acl = Acl(
        assessment_role="blue",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()

    response = client.get("/api/v1/acl/", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(str(a["user_id"]) == str(test_regular_user.id) for a in data)


def test_get_acl_by_id(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test retrieving a specific ACL (Admin only)
    """
    from app.models.acl import Acl

    new_acl = Acl(
        assessment_role="spectator",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()
    session.refresh(new_acl)

    response = client.get(f"/api/v1/acl/{new_acl.id}", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(new_acl.id)
    assert data["assessment_role"] == "spectator"


def test_update_acl(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test updating an ACL (Admin only)
    """
    from app.models.acl import Acl

    new_acl = Acl(
        assessment_role="spectator",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()
    session.refresh(new_acl)

    updated_role = "red"
    response = client.put(
        f"/api/v1/acl/{new_acl.id}",
        headers=auth_headers_admin,
        json={
            "assessment_role": updated_role,
            "user_id": str(test_regular_user.id),
            "assessment_id": str(assessment.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_role"] == updated_role

    # Verify in DB
    session.refresh(new_acl)
    assert new_acl.assessment_role == updated_role


def test_delete_acl(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test deleting an ACL (Admin only)
    """
    from app.models.acl import Acl

    new_acl = Acl(
        assessment_role="spectator",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()
    session.refresh(new_acl)
    acl_id = new_acl.id

    response = client.delete(f"/api/v1/acl/{acl_id}", headers=auth_headers_admin)
    assert response.status_code == 200
    assert response.json()["message"] == "Acl deleted successfully"

    # Verify deletion
    deleted_acl = session.get(Acl, acl_id)
    assert deleted_acl is None


def test_get_acls_by_assessment(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test retrieving all ACLs for a specific assessment (Admin only)
    """
    from app.models.acl import Acl

    # Create ACL
    new_acl = Acl(
        assessment_role="spectator",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()
    session.refresh(new_acl)

    response = client.get(
        f"/api/v1/acl/assessment/{assessment.id}", headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["assessment_id"] == str(assessment.id)
    assert data[0]["user_id"] == str(test_regular_user.id)


def test_get_acls_by_user(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    assessment: Assessment,
):
    """
    Test retrieving all ACLs for a specific user (Admin only)
    """
    from app.models.acl import Acl

    # Create ACL
    new_acl = Acl(
        assessment_role="spectator",
        user_id=test_regular_user.id,
        assessment_id=assessment.id,
        created_by=test_admin_user.id,
    )
    session.add(new_acl)
    session.commit()
    session.refresh(new_acl)

    response = client.get(
        f"/api/v1/acl/user/{test_regular_user.id}", headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["user_id"] == str(test_regular_user.id)
    assert data[0]["assessment_id"] == str(assessment.id)
