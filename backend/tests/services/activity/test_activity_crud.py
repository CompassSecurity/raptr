import uuid

import pytest
from fastapi import HTTPException

from app.enums.enums import ActivityState
from app.models.assessment import Assessment
from app.schemas.activity import ActivityCreate, ActivityFilter, ActivityUpdate
from app.schemas.activity_group import ActivityGroupBase
from app.services.activity.activity import (
    create_activity_service,
    get_activity_by_id_service,
    get_all_activities_service,
    toggle_delete_activity_service,
    toggle_visible_activity_service,
    update_activity_service,
)
from app.services.activity_group.activity_group import (
    create_activity_group_service,
    get_or_create_default_group,
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
    activity_data = ActivityCreate(
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


def test_create_activity_in_group(session, test_assessment, test_admin_user):
    group = create_activity_group_service(
        ActivityGroupBase(name="Target Group"),
        test_assessment.id,
        test_admin_user,
        session,
    )
    data = {"mitre_tactic": "T", "mitre_technique": "T1", "activity_group_id": group.id}

    first = create_activity_service(
        ActivityCreate(name="First", **data),
        test_assessment.id,
        test_admin_user,
        session,
    )
    second = create_activity_service(
        ActivityCreate(name="Second", **data),
        test_assessment.id,
        test_admin_user,
        session,
    )

    assert first.activity_group_id == group.id
    assert second.activity_group_id == group.id
    # New activities go to the end of the group
    assert second.activity_position > first.activity_position


def test_create_activity_without_group_uses_default(
    session, test_assessment, test_admin_user
):
    activity = create_activity_service(
        ActivityCreate(name="Activity", mitre_tactic="T", mitre_technique="T1"),
        test_assessment.id,
        test_admin_user,
        session,
    )
    default_group = get_or_create_default_group(test_assessment.id, session)
    assert activity.activity_group_id == default_group.id


def test_create_activity_in_invalid_group(session, test_assessment, test_admin_user):
    other_assessment = Assessment(
        name="Other Assessment",
        description="Description",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(other_assessment)
    session.commit()
    foreign_group = create_activity_group_service(
        ActivityGroupBase(name="Foreign Group"),
        other_assessment.id,
        test_admin_user,
        session,
    )

    # Unknown group and group of another assessment
    for group_id in (uuid.uuid4(), foreign_group.id):
        with pytest.raises(HTTPException) as exc:
            create_activity_service(
                ActivityCreate(
                    name="Activity",
                    mitre_tactic="T",
                    mitre_technique="T1",
                    activity_group_id=group_id,
                ),
                test_assessment.id,
                test_admin_user,
                session,
            )
        assert exc.value.status_code == 404


def test_get_all_activities(session, test_assessment, test_admin_user):
    a1 = ActivityCreate(name="Activity 1", mitre_tactic="T", mitre_technique="T1")
    a2 = ActivityCreate(name="Activity 2", mitre_tactic="T", mitre_technique="T2")

    create_activity_service(a1, test_assessment.id, test_admin_user, session)
    create_activity_service(a2, test_assessment.id, test_admin_user, session)

    results = get_all_activities_service(
        test_assessment.id, test_admin_user, session, ActivityFilter()
    )
    assert results.total == 2


def test_get_all_activities_with_filter(session, test_assessment, test_admin_user):
    a1 = ActivityCreate(name="Login Bruteforce", mitre_tactic="T", mitre_technique="T1")
    a2 = ActivityCreate(name="SQL Injection", mitre_tactic="T", mitre_technique="T2")

    create_activity_service(a1, test_assessment.id, test_admin_user, session)
    create_activity_service(a2, test_assessment.id, test_admin_user, session)

    results = get_all_activities_service(
        test_assessment.id, test_admin_user, session, ActivityFilter(name="Login")
    )
    assert results.total == 1
    assert results.items[0].name == "Login Bruteforce"


def test_get_activity_by_id(session, test_assessment, test_admin_user):
    activity_data = ActivityCreate(
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
    activity_data = ActivityCreate(
        name="Original", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )

    update_data = ActivityUpdate(
        name="Updated Name",
        mitre_tactic="Updated Tactic",
        mitre_technique="T9999",
        state=ActivityState.PENDING,
        activity_notes="New notes",
    )
    updated = update_activity_service(
        created.id, update_data, test_assessment.id, test_admin_user, session
    )

    assert updated.name == "Updated Name"
    assert updated.mitre_technique == "T9999"
    assert updated.activity_notes == "New notes"


def test_toggle_delete_activity(session, test_assessment, test_admin_user):
    activity_data = ActivityCreate(
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
    activity_data = ActivityCreate(
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


def test_set_visible_activity_explicit(session, test_assessment, test_admin_user):
    activity_data = ActivityCreate(
        name="Test Activity", mitre_tactic="T", mitre_technique="T1"
    )
    created = create_activity_service(
        activity_data, test_assessment.id, test_admin_user, session
    )
    assert created.visible is False

    toggle_visible_activity_service(
        created.id, test_assessment.id, test_admin_user, session, visible=True
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.visible is True
    updated_at = fetched.updated_at

    # Setting the same state again changes nothing, not even updated_at
    toggle_visible_activity_service(
        created.id, test_assessment.id, test_admin_user, session, visible=True
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.visible is True
    assert fetched.updated_at == updated_at

    toggle_visible_activity_service(
        created.id, test_assessment.id, test_admin_user, session, visible=False
    )
    fetched = get_activity_by_id_service(
        created.id, test_assessment.id, test_admin_user, session
    )
    assert fetched.visible is False
