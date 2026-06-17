import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.authentication import create_access_token_service
from app.models.acl import Acl
from app.models.activity import Activity
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
    session: Session,
    test_regular_user: User,
    test_assessment: Assessment,
    test_admin_user: User,
) -> Acl:
    """Create RED role ACL for regular user"""
    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=test_assessment.id,
        assessment_role="red",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()
    session.refresh(acl)
    return acl


@pytest.fixture(name="test_blue_user")
def test_blue_user_fixture(session: Session) -> User:
    """Create a blue user"""
    email = f"blue_{uuid.uuid4()}@example.com"
    user = User(email=email, hashed_password="hashed_password", role="user")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_acl_blue")
def test_acl_blue_fixture(
    session: Session,
    test_blue_user: User,
    test_assessment: Assessment,
    test_admin_user: User,
) -> Acl:
    """Create BLUE role ACL for blue user"""
    acl = Acl(
        user_id=test_blue_user.id,
        assessment_id=test_assessment.id,
        assessment_role="blue",
        created_by=test_admin_user.id,
    )
    session.add(acl)
    session.commit()
    session.refresh(acl)
    return acl


@pytest.fixture(name="auth_headers_blue")
def auth_headers_blue_fixture(test_blue_user: User) -> dict[str, str]:
    """Get auth headers for blue user"""
    access_token = create_access_token_service(data={"sub": test_blue_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="test_activity")
def test_activity_fixture(
    session: Session, test_assessment: Assessment, test_admin_user: User
) -> Activity:
    """Create a test activity"""
    # Create a visible activity group for the activity
    from app.models.activity_group import ActivityGroup

    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Test Group",
        visible=True,
        created_by=test_admin_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    activity = Activity(
        assessment_id=test_assessment.id,
        name="Test Activity",
        mitre_tactic="Execution",
        mitre_technique="T1204.001",
        provider="Test",
        priority="Medium",
        visible=True,
        state="Waiting Red",
        created_by=test_admin_user.id,
        activity_rationale="",
        activity_actions="",
        activity_requirements="",
        activity_notes="",
        expected_logging=False,
        expected_prevention=False,
        expected_alert_creation=False,
        expected_stakeholder_notification=False,
        expected_severity="Low",
        logged=False,
        prevented=False,
        alerted=False,
        alert_severity="Low",
        stakeholder_notification_created=False,
        stakeholder_notification_severity="Low",
        log_notes="",
        alert_notes="",
        prevent_notes="",
        stakeholder_notification_notes="",
        activity_group_id=group.id,  # Assign to group
    )

    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def test_red_user_update_restricted_fields(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_regular: dict[
        str, str
    ],  # Assuming this is the RED user from conftest/setup
    test_acl_red: Acl,  # Ensure RED ACL exists
):
    """Test RED user can update restricted fields like name"""
    update_data = {
        "name": "Red Updated Name",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "visible": True,
        "state": "Waiting Red",
        # PUT is full-replace; required fields (name, tactic, technique, state) MUST be
        # present. Other optional fields may be omitted.
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Red Updated Name"


def test_blue_user_update_success(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Test Blue user can update allowed fields when conditions are met"""
    # Activity is already Visible=True, Not Deleted, State="Waiting Red" from fixture

    update_data = {
        "name": "Test Activity",  # Required
        "mitre_tactic": "Execution",  # Required
        "mitre_technique": "T1204.001",  # Required
        "state": "Waiting Red",  # Required; activity is already in this state
        "log_notes": "Blue Log Notes",
        "alert_notes": "Blue Alert Notes",
        "logged": True,
        "prevented": True,
        "visible": True,
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["log_notes"] == "Blue Log Notes"
    assert data["alert_notes"] == "Blue Alert Notes"
    assert data["logged"] is True
    assert data["prevented"] is True
    # Regression: state must be preserved, not silently reset.
    assert data["state"] == "Waiting Red"


def test_blue_update_missing_state_rejected(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Omitting the required `state` key now returns 422 instead of nulling state."""
    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "log_notes": "Blue Log Notes",
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 422
    assert any(
        err.get("loc", [])[-1:] == ["state"] for err in response.json()["detail"]
    )


def test_blue_user_fail_hidden(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Test Blue user cannot update hidden activity"""
    test_activity.visible = False
    session.commit()

    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "log_notes": "Should Fail",
        "visible": True,
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_blue_user_fail_deleted(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Test Blue user cannot update deleted activity"""
    test_activity.deleted = True
    session.commit()

    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "log_notes": "Should Fail",
        "visible": True,
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_blue_user_fail_wrong_state(
    client: TestClient,
    session: Session,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Test Blue user cannot update activity in wrong state"""
    test_activity.state = "Pending"
    session.commit()

    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "log_notes": "Should Fail",
        "visible": True,
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 403
    assert "state must be one of" in response.json()["detail"]


def test_blue_user_restricted_field_ignored(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    auth_headers_blue: dict[str, str],
    test_acl_blue: Acl,
):
    """Test Blue user cannot update restricted fields, but request succeeds (fields ignored)"""

    update_data = {
        "name": "Blue Hacked Name",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "log_notes": "Blue Updated Notes",
        "visible": True,
        "state": "Waiting Red",
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 200
    assert response.json()["name"] != "Blue Hacked Name"
    assert response.json()["log_notes"] == "Blue Updated Notes"

    # Also check activity_notes which was specifically excluded
    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "activity_notes": "Secret Notes",
        "visible": True,
        "state": "Waiting Red",
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 200
    assert response.json()["activity_notes"] != "Secret Notes"

    # Also check expected_prevention
    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "expected_prevention": True,
        "visible": True,
        "state": "Waiting Red",
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 200
    assert response.json()["expected_prevention"] is False


def test_blue_user_invalid_state_payload(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_acl_blue: Acl,
    auth_headers_blue: dict[str, str],
):
    """Test Blue user sending invalid state gets 422"""
    # Pending is valid for Activity but invalid for Blue user (ActivityStateBlue)
    update_data = {
        "name": "Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "state": "Pending",
        "visible": True,
    }
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        json=update_data,
        headers=auth_headers_blue,
    )
    print(response.json())
    assert response.status_code == 422
    # Check that it looks like a Pydantic error
    assert "detail" in response.json()
    assert isinstance(response.json()["detail"], list)


def test_blue_user_update_tags(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_acl_blue: Acl,
    auth_headers_blue: dict[str, str],
):
    """Test Blue user can update tags (uses same permission check)"""
    # This verifies that validate_activity_update_permission works without activity body conflict
    update_data = {"tag_ids": []}
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/tags",
        json=update_data,
        headers=auth_headers_blue,
    )
    assert response.status_code == 200
