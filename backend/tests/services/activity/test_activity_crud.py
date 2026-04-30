import uuid

import pytest
from fastapi import HTTPException

from app.models.assessment import Assessment
from app.schemas.activity import ActivityBase, ActivityFilter, ActivityUpdate
from app.services.activity.activity import (
    create_activity_service,
    get_activity_by_id_service,
    get_all_activities_service,
    toggle_delete_activity_service,
    toggle_visible_activity_service,
    update_activity_service,
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


def test_create_activity(session, test_assessment, test_admin_user):
    activity_data = ActivityBase(
        name="Test Activity",
        mitre_tactic="Initial Access",
        mitre_technique="T1190",
    )
    activity = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    assert activity.name == "Test Activity"
    assert activity.mitre_tactic == "Initial Access"
    assert activity.mitre_technique == "T1190"
    assert activity.assessment_id == test_assessment.id


def test_get_all_activities(session, test_assessment, test_admin_user):
    a1 = ActivityBase(name="Activity 1", mitre_tactic="T", mitre_technique="T1")
    a2 = ActivityBase(name="Activity 2", mitre_tactic="T", mitre_technique="T2")

    create_activity_service(a1, test_assessment.id, test_admin_user, session)
    create_activity_service(a2, test_assessment.id, test_admin_user, session)

    results = get_all_activities_service(
        test_assessment.id, test_admin_user, session, ActivityFilter()
    )
    assert results.total == 2


def test_get_all_activities_with_filter(session, test_assessment, test_admin_user):
    a1 = ActivityBase(name="Login Bruteforce", mitre_tactic="T", mitre_technique="T1")
    a2 = ActivityBase(name="SQL Injection", mitre_tactic="T", mitre_technique="T2")

    create_activity_service(a1, test_assessment.id, test_admin_user, session)
    create_activity_service(a2, test_assessment.id, test_admin_user, session)

    results = get_all_activities_service(
        test_assessment.id, test_admin_user, session, ActivityFilter(name="Login")
    )
    assert results.total == 1
    assert results.items[0].name == "Login Bruteforce"


def test_get_activity_by_id(session, test_assessment, test_admin_user):
    activity_data = ActivityBase(
        name="Test Activity", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.id == created.id
    assert fetched.name == "Test Activity"


def test_get_activity_by_id_not_found(session, test_assessment, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        get_activity_by_id_service(
            uuid.uuid4(), test_assessment.id, test_admin_user, session
        )
    assert exc.value.status_code == 404


def test_update_activity(session, test_assessment, test_admin_user):
    activity_data = ActivityBase(
        name="Original", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    update_data = ActivityUpdate(
        name="Updated Name",
        mitre_tactic="Updated Tactic",
        mitre_technique="T9999",
        activity_notes="New notes",
    )
    updated = update_activity_service(
        created.id, update_data, test_assessment.id, test_admin_user, session
    )

    assert updated.name == "Updated Name"
    assert updated.mitre_technique == "T9999"
    assert updated.activity_notes == "New notes"


def test_toggle_delete_activity(session, test_assessment, test_admin_user):
    activity_data = ActivityBase(
        name="Test Activity", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    assert created.deleted is False

    # Delete
    toggle_delete_activity_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.deleted is True

    # Undelete
    toggle_delete_activity_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.deleted is False


def test_toggle_visible_activity(session, test_assessment, test_admin_user):
    activity_data = ActivityBase(
        name="Test Activity", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    assert created.visible is False

    # Make visible
    toggle_visible_activity_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.visible is True

    # Make invisible
    toggle_visible_activity_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.visible is False
