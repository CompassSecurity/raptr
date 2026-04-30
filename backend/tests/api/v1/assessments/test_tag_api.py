import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.acl import Acl
from app.models.assessment import Assessment
from app.models.user import User


@pytest.fixture(name="test_assessment")
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    assessment = Assessment(
        name="Test Assessment",
        description="Test Description",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


@pytest.fixture(name="test_acl_blue")
def test_acl_blue_fixture(
    session: Session, test_regular_user: User, test_assessment: Assessment
) -> Acl:
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role="blue",
        created_by=test_regular_user.id,
    )
    session.add(acl)
    session.commit()
    session.refresh(acl)
    return acl


@pytest.fixture(name="test_acl_spectator")
def test_acl_spectator_fixture(session: Session, test_assessment: Assessment) -> Acl:
    from app.core.password import hash_password

    spectator_user = User(
        email="spectator@test.com",
        hashed_password=hash_password("SpectatorPass123!"),
        role="user",
        disabled=False,
    )
    session.add(spectator_user)
    session.commit()
    session.refresh(spectator_user)

    acl = Acl(
        user_id=spectator_user.id,
        assessment_id=test_assessment.id,
        assessment_role="spectator",
        created_by=spectator_user.id,
    )
    session.add(acl)
    session.commit()
    session.refresh(acl)
    return acl


@pytest.fixture(name="auth_headers_spectator")
def auth_headers_spectator_fixture(
    session: Session, test_acl_spectator: Acl
) -> dict[str, str]:
    from datetime import timedelta

    from app.core.authentication import create_access_token_service

    spectator_user = session.get(User, test_acl_spectator.user_id)
    access_token = create_access_token_service(
        data={"sub": spectator_user.email}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_create_tag(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "Test Tag", "color": "#FF0000"},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Tag"
    assert data["color"] == "#FF0000"
    assert "id" in data


def test_create_tag_insufficient_permissions(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_spectator: Acl,
    auth_headers_spectator: dict[str, str],
):
    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "Test Tag", "color": "#FF0000"},
        headers=auth_headers_spectator,
    )
    assert response.status_code == 403


def test_get_tags(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    # Create a tag first
    client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "Tag 1", "color": "#000000"},
        headers=auth_headers_regular,
    )

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["name"] == "Tag 1"


def test_get_tag_by_id(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    create_resp = client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "Tag By ID", "color": "#000000"},
        headers=auth_headers_regular,
    )
    tag_id = create_resp.json()["id"]

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/tag/{tag_id}",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    assert response.json()["id"] == tag_id


def test_update_tag(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    create_resp = client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "Original Name", "color": "#000000"},
        headers=auth_headers_regular,
    )
    tag_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/tag/{tag_id}",
        json={"name": "Updated Name", "color": "#FFFFFF"},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["color"] == "#FFFFFF"


def test_delete_tag(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    create_resp = client.post(
        f"/api/v1/assessments/{test_assessment.id}/tag/",
        json={"name": "To Delete", "color": "#000000"},
        headers=auth_headers_regular,
    )
    tag_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/tag/{tag_id}/delete",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200

    # Verify deletion by trying to get it, usually returns 404 or soft deleted (depends on implementation)
    # The service raises 404 if not found. Let's assume soft delete makes it 'not found' for get_by_id?
    # Checking app/services/tag/tag.py: get_tag_by_id_service checks "deleted.is_(False)"?
    # Actually I checked earlier, get_tag_by_id_service does NOT check deleted=False in the select statement explicitly showed in my view_file output.
    # WAIT, I missed re-verifying that.
    # Let's check test_tag.py again. In test_delete_tag, I asserted fetched_tag.deleted is True.
    # So the API will return it but with deleted=True?
    # Let's see what get_tag_by_id_service returns.

    # Re-verify logic:
    # If I call GET /tag/{id}, and it returns the tag, I check if deleted is True.

    get_response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/tag/{tag_id}",
        headers=auth_headers_regular,
    )
    assert get_response.status_code == 200
    assert get_response.json()["deleted"] is True
