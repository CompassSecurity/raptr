import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.acl import Acl
from app.models.activity import Activity
from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.user import User


@pytest.fixture(name="test_assessment")
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    """Create a test assessment"""
    assessment = Assessment(
        name="Test Assessment Group Assign",
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


@pytest.fixture(name="test_activity")
def test_activity_fixture(
    session: Session, test_assessment: Assessment, test_admin_user: User
) -> Activity:
    """Create a test activity"""
    activity = Activity(
        assessment_id=test_assessment.id,
        name="Test Activity",
        mitre_tactic="Execution",
        mitre_technique="T1204.001",
        provider="Test Provider",
        created_by=test_admin_user.id,
        priority="Low",
        state="Pending",
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
    )

    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


@pytest.fixture(name="test_group")
def test_group_fixture(
    session: Session, test_assessment: Assessment, test_admin_user: User
) -> ActivityGroup:
    """Create a test activity group"""
    group = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Test Group",
        created_by=test_admin_user.id,
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def test_assign_activity_to_group(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_group: ActivityGroup,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Test assigning an activity to a group"""
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/activity_group",
        json={"activity_group_id": str(test_group.id)},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["activity_group_id"] == str(test_group.id)

    # Verify DB
    session.refresh(test_activity)
    assert test_activity.activity_group_id == test_group.id


def test_remove_activity_from_group(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_group: ActivityGroup,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Test removing an activity from a group moves it to the default group"""
    # Setup: Assign first
    test_activity.activity_group_id = test_group.id
    session.add(test_activity)
    session.commit()

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/activity_group",
        json={"activity_group_id": None},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    # Activity moves to default group, not None
    assert data["activity_group_id"] is not None
    assert data["activity_group_id"] != str(test_group.id)

    # Verify DB - activity is in the default group
    session.refresh(test_activity)
    assert test_activity.activity_group_id is not None
    assert test_activity.activity_group_id != test_group.id

    # Verify the group is the default group
    default_group = session.get(ActivityGroup, test_activity.activity_group_id)
    assert default_group is not None
    assert default_group.is_default is True


def test_change_activity_group(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_group: ActivityGroup,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
    test_admin_user: User,
    session: Session,
):
    """Test changing from one group to another"""
    # Second group
    group2 = ActivityGroup(
        assessment_id=test_assessment.id,
        name="Group 2",
        created_by=test_admin_user.id,
    )
    session.add(group2)
    session.commit()

    # Assign to first group
    test_activity.activity_group_id = test_group.id
    session.add(test_activity)
    session.commit()

    # Change to second group
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/activity_group",
        json={"activity_group_id": str(group2.id)},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["activity_group_id"] == str(group2.id)

    # Verify DB
    session.refresh(test_activity)
    assert test_activity.activity_group_id == group2.id
