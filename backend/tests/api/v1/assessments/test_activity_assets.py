import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums.enums import ActivityAssetRole
from app.models.acl import Acl
from app.models.activity import Activity
from app.models.assessment import Assessment
from app.models.asset import Asset
from app.models.user import User


@pytest.fixture(name="test_assessment")
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    """Create a test assessment"""
    assessment = Assessment(
        name="Test Assessment Asset",
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
    """Create BLUE role ACL for regular user"""
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
        provider="Test Provider",
        created_by=test_admin_user.id,
        priority="Low",
        state="Waiting Blue",
        visible=True,
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


@pytest.fixture(name="test_assets")
def test_assets_fixture(
    session: Session, test_assessment: Assessment, test_admin_user: User
) -> list[Asset]:
    """Create test assets"""
    assets = []
    for i in range(3):
        asset = Asset(
            assessment_id=test_assessment.id,
            name=f"Asset {i}",
            created_by=test_admin_user.id,
        )
        session.add(asset)
        assets.append(asset)
    session.commit()
    for asset in assets:
        session.refresh(asset)
    return assets


def test_assign_assets_success(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_assets: list[Asset],
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Test assigning assets to an activity"""
    # Assign first two assets as SOURCE
    asset_ids = [str(test_assets[0].id), str(test_assets[1].id)]

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.SOURCE.value}",
        json={"asset_ids": asset_ids},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    assert (
        response.json()["message"]
        == f"Assets assigned to activity as {ActivityAssetRole.SOURCE.value}"
    )

    # Verify directly via DB
    session.expire_all()
    session.refresh(test_activity)
    # The relationship needs to be loaded. Accessing it should trigger lazy load or use verify via API
    # Testing via another endpoint is better to verifying the full loop

    # Use the GET Activity endpoint to verify
    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()

    # Check "sources" field (mapped from SOURCE role)
    assert "sources" in data
    assets = data["sources"]
    assert len(assets) == 2
    returned_ids = {item["id"] for item in assets}
    assert str(test_assets[0].id) in returned_ids
    assert str(test_assets[1].id) in returned_ids


def test_replace_assets(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_assets: list[Asset],
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    """Test replacing assets for a role"""
    # First assignment
    client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.TARGET.value}",
        json={"asset_ids": [str(test_assets[0].id)]},
        headers=auth_headers_regular,
    )

    # Replace with different asset
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.TARGET.value}",
        json={"asset_ids": [str(test_assets[1].id)]},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200

    # Verify only second asset is present via GET Activity
    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        headers=auth_headers_regular,
    )
    data = response.json()
    # Check "targets" field (mapped from TARGET role)
    assert "targets" in data
    assets = data["targets"]
    assert len(assets) == 1
    assert assets[0]["id"] == str(test_assets[1].id)


def test_clear_assets(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_assets: list[Asset],
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
):
    """Test clearing assets for a role"""
    # Assign asset
    client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.TOOL.value}",
        json={"asset_ids": [str(test_assets[0].id)]},
        headers=auth_headers_regular,
    )

    # Clear assets (send empty list)
    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.TOOL.value}",
        json={"asset_ids": []},
        headers=auth_headers_regular,
    )
    assert response.status_code == 200

    # Verify empty via GET Activity
    response = client.get(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}",
        headers=auth_headers_regular,
    )
    data = response.json()
    # Check "tools" field (mapped from TOOL role)
    assert "tools" in data
    assets = data["tools"]
    assert len(assets) == 0


def test_invalid_asset_assignment(
    client: TestClient,
    test_assessment: Assessment,
    test_activity: Activity,
    test_acl_blue: Acl,
    auth_headers_regular: dict[str, str],
    test_admin_user: User,
    session: Session,
):
    """Test assigning asset from different assessment (should fail)"""
    # Create asset in different assessment
    other_assessment = Assessment(
        name="Other",
        description="Other Description",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(other_assessment)
    session.commit()

    other_asset = Asset(
        assessment_id=other_assessment.id,
        name="Other Asset",
        created_by=test_admin_user.id,
    )
    session.add(other_asset)
    session.commit()

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity.id}/assets/{ActivityAssetRole.SOURCE.value}",
        json={"asset_ids": [str(other_asset.id)]},
        headers=auth_headers_regular,
    )

    # Depending on implementation, might be 404 or 400. Service raises 404 if not found/wrong assessment
    assert response.status_code == 404
