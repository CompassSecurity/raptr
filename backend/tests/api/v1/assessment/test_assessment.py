from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User

# Test data
ASSESSMENT_NAME = "Test Assessment"
ASSESSMENT_DESC = "This is a test assessment"
ASSESSMENT_TYPE = "PurpleTeam"


def test_create_assessment(
    client: TestClient, auth_headers_admin: dict[str, str], session: Session
):
    """
    Test creating a new assessment (Admin only)
    """
    response = client.post(
        "/api/v1/assessment/",
        headers=auth_headers_admin,
        json={
            "name": ASSESSMENT_NAME,
            "description": ASSESSMENT_DESC,
            "assessment_type": ASSESSMENT_TYPE,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == ASSESSMENT_NAME
    assert data["description"] == ASSESSMENT_DESC
    assert data["assessment_type"] == ASSESSMENT_TYPE
    assert "id" in data


def test_create_assessment_regular_user(
    client: TestClient, auth_headers_regular: dict[str, str]
):
    """
    Test that a regular user cannot create an assessment
    """
    response = client.post(
        "/api/v1/assessment/",
        headers=auth_headers_regular,
        json={
            "name": ASSESSMENT_NAME,
            "description": ASSESSMENT_DESC,
            "assessment_type": ASSESSMENT_TYPE,
        },
    )
    assert response.status_code == 403


def test_get_assessments(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
):
    """
    Test retrieving all assessments
    """
    # First create an assessment (using admin headers or direct DB)
    from app.models.acl import Acl
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Get Test",
        description="Desc",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()

    # Create ACL for regular user
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=new_assessment.id,
        assessment_role="viewer",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()

    response = client.get("/api/v1/assessment/", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["total"] >= 1
    assert any(a["name"] == "Get Test" for a in data["items"])


def test_get_assessment_by_id(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
):
    """
    Test retrieving a specific assessment
    """
    from app.models.acl import Acl
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Get One Test",
        description="Desc One",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()
    session.refresh(new_assessment)

    # Create ACL for regular user
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=new_assessment.id,
        assessment_role="viewer",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()

    response = client.get(
        f"/api/v1/assessment/{new_assessment.id}", headers=auth_headers_regular
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(new_assessment.id)
    assert data["name"] == "Get One Test"


def test_update_assessment(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
):
    """
    Test updating an assessment (Admin only)
    """
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Update Test",
        description="Original Desc",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()
    session.refresh(new_assessment)

    updated_name = "Updated Name"
    response = client.put(
        f"/api/v1/assessment/{new_assessment.id}",
        headers=auth_headers_admin,
        json={
            "name": updated_name,
            "description": "Original Desc",
            "assessment_type": "RedTeam",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == updated_name

    # Verify in DB
    session.refresh(new_assessment)
    assert new_assessment.name == updated_name


def test_update_assessment_regular_user(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    session: Session,
    test_admin_user: User,
):
    """
    Test that a regular user cannot update an assessment
    """
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Update Test Reg",
        description="Desc",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()
    session.refresh(new_assessment)

    response = client.put(
        f"/api/v1/assessment/{new_assessment.id}",
        headers=auth_headers_regular,
        json={"name": "Hacked", "description": "Desc", "assessment_type": "RedTeam"},
    )
    assert response.status_code == 404


def test_delete_assessment(
    client: TestClient,
    auth_headers_admin: dict[str, str],
    session: Session,
    test_admin_user: User,
):
    """
    Test deleting an assessment (Admin only)
    """
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Delete Test",
        description="Desc",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()
    session.refresh(new_assessment)
    assessment_id = new_assessment.id

    response = client.delete(
        f"/api/v1/assessment/{assessment_id}", headers=auth_headers_admin
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Assessment deleted successfully"

    # Verify deletion
    deleted_assessment = session.get(Assessment, assessment_id)
    assert deleted_assessment is None


def test_delete_assessment_regular_user(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    session: Session,
    test_admin_user: User,
):
    """
    Test that a regular user cannot delete an assessment
    """
    from app.models.assessment import Assessment

    new_assessment = Assessment(
        name="Delete Test Reg",
        description="Desc",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(new_assessment)
    session.commit()
    session.refresh(new_assessment)

    response = client.delete(
        f"/api/v1/assessment/{new_assessment.id}", headers=auth_headers_regular
    )
    assert response.status_code == 403
