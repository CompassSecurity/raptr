"""
Tests for optimistic concurrency control on activity updates.
Verifies that the backend correctly detects stale writes using updated_at.
"""

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.acl import Acl
from app.models.activity import Activity
from app.models.assessment import Assessment
from app.models.user import User


@pytest.fixture(name="test_assessment")
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    """Create a test assessment"""
    assessment = Assessment(
        name="Concurrency Test Assessment",
        description="Testing concurrent edits",
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
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    auth_headers_regular: dict[str, str],
) -> dict:
    """Create a test activity via the API and return the response JSON."""
    activity_data = {
        "name": "Concurrency Test Activity",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
    }
    response = client.post(
        f"/api/v1/assessments/{test_assessment.id}/activity/",
        json=activity_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    return response.json()


def test_update_with_matching_updated_at(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_activity: dict,
    auth_headers_regular: dict[str, str],
):
    """Sending correct updated_at should succeed with 200 OK."""
    update_data = {
        "name": "Updated Name",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "updated_at": test_activity["updated_at"],
    }

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=update_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_update_with_stale_updated_at(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_activity: dict,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Sending an outdated updated_at should fail with 409 Conflict."""
    original_updated_at = test_activity["updated_at"]

    # First update — should succeed and change updated_at
    first_update = {
        "name": "First Update",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "updated_at": original_updated_at,
    }
    response1 = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=first_update,
        headers=auth_headers_regular,
    )
    assert response1.status_code == 200

    # Manually bump the timestamp in DB to simulate time passing/concurrent edit
    # We cast to UUID because test_activity['id'] is a string
    activity_db = session.get(Activity, uuid.UUID(test_activity["id"]))
    activity_db.updated_at = activity_db.updated_at + timedelta(seconds=1)
    session.commit()
    session.refresh(activity_db)

    # Second update using the original (now stale) updated_at — should fail
    stale_update = {
        "name": "Second Update (should conflict)",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        "updated_at": original_updated_at,
    }
    response2 = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=stale_update,
        headers=auth_headers_regular,
    )
    assert response2.status_code == 409
    assert "modified by another user" in response2.json()["detail"]


def test_update_without_updated_at(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_activity: dict,
    auth_headers_regular: dict[str, str],
):
    """Omitting updated_at should succeed (backward compatibility)."""
    update_data = {
        "name": "No Concurrency Check",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1204.001",
        # No updated_at field
    }

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=update_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "No Concurrency Check"


def test_updated_at_bumps_on_asset_only_change(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_activity: dict,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Changing only linked assets (sources) should still bump updated_at."""
    from sqlalchemy import select as sa_select

    from app.models.asset import Asset
    from app.models.user import User as UserModel

    # Create an asset to assign
    user_id = session.execute(sa_select(UserModel.id)).scalars().first()
    asset = Asset(
        assessment_id=test_assessment.id,
        name="Test Asset",
        created_by=user_id,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)

    original_updated_at = test_activity["updated_at"]

    # Update with only a source change (all other fields unchanged)
    update_data = {
        "name": test_activity["name"],
        "mitre_tactic": test_activity["mitre_tactic"],
        "mitre_technique": test_activity["mitre_technique"],
        "updated_at": original_updated_at,
        "sources": [str(asset.id)],
    }

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=update_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) == 1

    # Manually bump the timestamp in DB to simulate time passing/concurrent edit
    activity_db = session.get(Activity, uuid.UUID(test_activity["id"]))
    activity_db.updated_at = activity_db.updated_at + timedelta(seconds=1)
    session.commit()
    session.refresh(activity_db)

    # Now a stale update should fail with 409
    stale_update = {
        "name": test_activity["name"],
        "mitre_tactic": test_activity["mitre_tactic"],
        "mitre_technique": test_activity["mitre_technique"],
        "updated_at": original_updated_at,  # stale
    }
    response2 = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=stale_update,
        headers=auth_headers_regular,
    )
    assert response2.status_code == 409


def test_updated_at_bumps_on_evaluation_only_change(
    client: TestClient,
    test_assessment: Assessment,
    test_acl_red: Acl,
    test_activity: dict,
    auth_headers_regular: dict[str, str],
    session: Session,
):
    """Changing only evaluation fields should still bump updated_at."""
    original_updated_at = test_activity["updated_at"]

    # Set the input fields that drive evaluation calculation.
    # expected_logging=True + logged=True → logged_evaluation="pass"
    update_data = {
        "name": test_activity["name"],
        "mitre_tactic": test_activity["mitre_tactic"],
        "mitre_technique": test_activity["mitre_technique"],
        "updated_at": original_updated_at,
        "expected_logging": True,
        "logged": True,
    }

    response = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=update_data,
        headers=auth_headers_regular,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation"]["logged_evaluation"] == "pass"
    assert data["evaluation"]["activity_coverage_score"] == 100

    # Manually bump the timestamp in DB to simulate time passing/concurrent edit
    activity_db = session.get(Activity, uuid.UUID(test_activity["id"]))
    activity_db.updated_at = activity_db.updated_at + timedelta(seconds=1)
    session.commit()
    session.refresh(activity_db)

    # Stale update with original timestamp should now conflict
    stale_update = {
        "name": test_activity["name"],
        "mitre_tactic": test_activity["mitre_tactic"],
        "mitre_technique": test_activity["mitre_technique"],
        "updated_at": original_updated_at,  # stale
    }
    response2 = client.put(
        f"/api/v1/assessments/{test_assessment.id}/activity/{test_activity['id']}",
        json=stale_update,
        headers=auth_headers_regular,
    )
    assert response2.status_code == 409
