import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.acl import Acl
from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.user import User


@pytest.fixture(name="test_assessment")
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    """Create a test assessment"""
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


@pytest.fixture(name="test_acl_red")
def test_acl_red_fixture(
    session: Session, test_regular_user: User, test_assessment: Assessment
) -> Acl:
    """Create RED role ACL for regular user"""
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role="red",
        created_by=test_regular_user.id,
    )
    session.add(acl)
    session.commit()
    session.refresh(acl)
    return acl


@pytest.fixture(name="test_acl_spectator")
def test_acl_spectator_fixture(session: Session, test_assessment: Assessment) -> Acl:
    """Create SPECTATOR role ACL for a test user"""
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
    """Generate authorization headers for spectator user"""
    from datetime import timedelta

    from app.core.authentication import create_access_token_service

    spectator_user = session.get(User, test_acl_spectator.user_id)
    access_token = create_access_token_service(
        data={"sub": spectator_user.email}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_create_activity_group(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
):
    """Test creating an activity group with RED role"""
    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/",
        json={"name": "Test Activity Group", "visible": False},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Activity Group"
    assert not data["visible"]
    assert "id" in data


def test_create_activity_group_insufficient_permissions(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_spectator: Acl,
    auth_headers_spectator: dict[str, str],
):
    """Test that SPECTATOR cannot create activity groups"""
    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/",
        json={"name": "Test Group", "visible": True},
        headers=auth_headers_spectator,
    )
    assert response.status_code == 403


def test_get_all_activity_groups(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test getting all activity groups"""
    # Create test groups
    group1 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Group 1",
        visible=True,
        created_by=test_regular_user.id,
    )
    group2 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Group 2",
        visible=False,
        created_by=test_regular_user.id,
    )
    session.add_all([group1, group2])
    session.commit()

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # RED can see both


def test_get_activity_groups_visibility_filtering(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_spectator: Acl,
    test_regular_user: User,
    auth_headers_spectator: dict[str, str],
):
    """Test that SPECTATOR can only see visible groups"""
    # Create test groups
    group1 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Visible Group",
        visible=True,
        created_by=test_regular_user.id,
    )
    group2 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Hidden Group",
        visible=False,
        created_by=test_regular_user.id,
    )
    session.add_all([group1, group2])
    session.commit()

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/",
        headers=auth_headers_spectator,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Only visible group
    assert data[0]["name"] == "Visible Group"


def test_get_activity_group_by_id(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test getting a specific activity group"""
    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Test Group",
        visible=True,
        created_by=test_regular_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/{group.id}",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Group"
    assert data["id"] == str(group.id)


def test_get_activity_group_activities_empty(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test that empty activity group returns empty array, not 404"""
    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Empty Group",
        visible=True,
        created_by=test_regular_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/{group.id}/activities",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data == []  # Empty array, not 404


def test_update_activity_group(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test updating an activity group"""
    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Original Name",
        visible=False,
        created_by=test_regular_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/{group.id}",
        json={"name": "Updated Name", "visible": True},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["visible"]


def test_delete_activity_group(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test soft deleting an activity group"""
    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="To Delete",
        visible=True,
        created_by=test_regular_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/{group.id}/delete",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200

    # Verify soft delete
    session.refresh(group)
    assert group.deleted
    assert group.deleted_by == test_regular_user.id


def test_cannot_delete_default_group(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test that the default activity group cannot be deleted"""
    default_group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Ungrouped",
        visible=True,
        is_default=True,
        created_by=test_regular_user.id,
    )
    session.add(default_group)
    session.commit()
    session.refresh(default_group)

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/{default_group.id}/delete",
        headers=auth_headers_regular,
    )
    assert response.status_code == 400
    assert "Cannot delete the default activity group" in response.json()["detail"]


def test_create_activity_assigns_to_default_group(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Test that creating an activity automatically assigns it to the default group"""
    activity_data = {
        "name": "Test Activity Default Group",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
    }

    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/activity/",
        json=activity_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["activity_group_id"] is not None

    # Verify it's in a default group
    group = session.get(ActivityGroup, uuid.UUID(data["activity_group_id"]))
    assert group is not None
    assert group.is_default is True
    assert group.name == "Ungrouped"


def test_get_activity_groups_name_filtering(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """Test filtering activity groups by name"""
    # Create test groups
    group1 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Alpha Group",
        visible=True,
        created_by=test_regular_user.id,
    )
    group2 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Beta Group",
        visible=True,
        created_by=test_regular_user.id,
    )
    session.add_all([group1, group2])
    session.commit()

    # Filter for "Alpha"
    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/?name=Alpha",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alpha Group"

    # Filter for "Group" (should return both)
    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity_group/?name=Group",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Might include default group if created
    names = [g["name"] for g in data]
    assert "Alpha Group" in names
    assert "Beta Group" in names
