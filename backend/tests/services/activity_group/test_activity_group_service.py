import uuid

import pytest
from fastapi import HTTPException

from app.models.activity import Activity
from app.models.assessment import Assessment
from app.schemas.activity_group import ActivityGroupBase, ActivityGroupFilter
from app.services.activity_group.activity_group import (
    assign_activity_to_activity_group_service,
    create_activity_group_service,
    get_activity_group_activities_service,
    get_activity_group_by_id_service,
    get_activity_group_service,
    remove_activity_from_activity_group_service,
    reorder_activities_service,
    reorder_activity_groups_service,
    toggle_activity_group_delete_service,
    toggle_activity_group_visible_service,
    update_activity_group_service,
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


def test_create_activity_group(session, test_assessment, test_admin_user):
    group_data = ActivityGroupBase(name="Test Group")
    group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    assert group.name == "Test Group"
    assert group.assessment_id == test_assessment.id
    assert group.deleted is False
    assert group.visible is False


def test_get_activity_groups(session, test_assessment, test_admin_user):
    group1 = ActivityGroupBase(name="Group 1")
    group2 = ActivityGroupBase(name="Group 2")

    create_activity_group_service(group1, test_assessment.id, test_admin_user, session)
    create_activity_group_service(group2, test_assessment.id, test_admin_user, session)

    groups = get_activity_group_service(
        test_assessment.id, test_admin_user, session, ActivityGroupFilter()
    )
    assert len(groups) == 2


def test_get_activity_groups_with_query(session, test_assessment, test_admin_user):
    group1 = ActivityGroupBase(name="Alpha Group")
    group2 = ActivityGroupBase(name="Beta Group")

    create_activity_group_service(group1, test_assessment.id, test_admin_user, session)
    create_activity_group_service(group2, test_assessment.id, test_admin_user, session)

    groups = get_activity_group_service(
        test_assessment.id,
        test_admin_user,
        session,
        ActivityGroupFilter(name="Alpha"),
    )
    assert len(groups) == 1
    assert groups[0].name == "Alpha Group"


def test_get_activity_group_by_id(session, test_assessment, test_admin_user):
    group_data = ActivityGroupBase(name="Test Group")
    created_group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    fetched_group = get_activity_group_by_id_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_group.id == created_group.id
    assert fetched_group.name == "Test Group"


def test_get_activity_group_by_id_not_found(session, test_assessment, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        get_activity_group_by_id_service(
            uuid.uuid4(), test_assessment.id, test_admin_user, session
        )
    assert exc.value.status_code == 404


def test_update_activity_group(session, test_assessment, test_admin_user):
    group_data = ActivityGroupBase(name="Original Name")
    created_group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    update_data = ActivityGroupBase(name="Updated Name")
    updated_group = update_activity_group_service(
        created_group.id, update_data, test_assessment.id, test_admin_user, session
    )

    assert updated_group.name == "Updated Name"


def test_toggle_activity_group_delete(session, test_assessment, test_admin_user):
    group_data = ActivityGroupBase(name="Test Group")
    created_group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    # Delete
    toggle_activity_group_delete_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    fetched_group = get_activity_group_by_id_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_group.deleted is True

    # Undelete
    toggle_activity_group_delete_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    fetched_group = get_activity_group_by_id_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_group.deleted is False


def test_toggle_activity_group_visible(session, test_assessment, test_admin_user):
    group_data = ActivityGroupBase(name="Test Group")
    created_group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    assert created_group.visible is False

    # Make visible
    toggle_activity_group_visible_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    fetched_group = get_activity_group_by_id_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_group.visible is True

    # Make invisible
    toggle_activity_group_visible_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    fetched_group = get_activity_group_by_id_service(
        created_group.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_group.visible is False


def test_assign_activity_to_group(session, test_assessment, test_admin_user):
    # Create group
    group_data = ActivityGroupBase(name="Test Group")
    group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    # Create activity
    activity = Activity(
        assessment_id=test_assessment.id,
        name="Test Activity",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        created_by=test_admin_user.id,
    )
    session.add(activity)
    session.commit()

    # Assign
    assign_activity_to_activity_group_service(
        activity.id, group.id, test_assessment.id, test_admin_user, session
    )

    session.refresh(activity)
    assert activity.activity_group_id == group.id


def test_remove_activity_from_group(session, test_assessment, test_admin_user):
    # Create group
    group_data = ActivityGroupBase(name="Test Group")
    group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    # Create activity assigned to group
    activity = Activity(
        assessment_id=test_assessment.id,
        name="Test Activity",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        activity_group_id=group.id,
        created_by=test_admin_user.id,
    )
    session.add(activity)
    session.commit()

    # Remove from group — activity moves to default group
    remove_activity_from_activity_group_service(
        activity.id, test_assessment.id, test_admin_user, session
    )

    session.refresh(activity)
    assert activity.activity_group_id is not None
    assert activity.activity_group_id != group.id

    # Verify it's in the default group
    from app.models.activity_group import ActivityGroup

    default_group = session.get(ActivityGroup, activity.activity_group_id)
    assert default_group is not None
    assert default_group.is_default is True


def test_get_activity_group_activities(session, test_assessment, test_admin_user):
    # Create group
    group_data = ActivityGroupBase(name="Test Group")
    group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    # Create activities in group
    a1 = Activity(
        assessment_id=test_assessment.id,
        name="Activity 1",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        activity_group_id=group.id,
        created_by=test_admin_user.id,
    )
    a2 = Activity(
        assessment_id=test_assessment.id,
        name="Activity 2",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        activity_group_id=group.id,
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.commit()

    activities = get_activity_group_activities_service(
        group.id, test_assessment.id, test_admin_user, session
    )
    assert len(activities) == 2


def test_reorder_activity_group(session, test_assessment, test_admin_user):
    # Create group
    group_data = ActivityGroupBase(name="Test Group")
    group = create_activity_group_service(
        group_data, test_assessment.id, test_admin_user, session
    )

    # Create activities in group
    a1 = Activity(
        assessment_id=test_assessment.id,
        name="Activity 1",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        activity_group_id=group.id,
        activity_position=0,
        created_by=test_admin_user.id,
    )
    a2 = Activity(
        assessment_id=test_assessment.id,
        name="Activity 2",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        activity_group_id=group.id,
        activity_position=1,
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.commit()

    # Reorder: a2 first, then a1
    reorder_activities_service(
        group.id, [a2.id, a1.id], test_assessment.id, test_admin_user, session
    )

    session.refresh(a1)
    session.refresh(a2)
    assert a2.activity_position == 0
    assert a1.activity_position == 1


def test_reorder_activity_groups(session, test_assessment, test_admin_user):
    # Create groups
    g1 = create_activity_group_service(
        ActivityGroupBase(name="Group 1"), test_assessment.id, test_admin_user, session
    )
    g2 = create_activity_group_service(
        ActivityGroupBase(name="Group 2"), test_assessment.id, test_admin_user, session
    )
    g3 = create_activity_group_service(
        ActivityGroupBase(name="Group 3"), test_assessment.id, test_admin_user, session
    )

    # Initial order check (default position is 0, 1, 2)
    assert g1.activity_group_position == 0
    assert g2.activity_group_position == 1
    assert g3.activity_group_position == 2

    # Reorder: g3, g1, g2
    reorder_activity_groups_service(
        [g3.id, g1.id, g2.id], test_assessment.id, test_admin_user, session
    )

    session.refresh(g1)
    session.refresh(g2)
    session.refresh(g3)

    assert g3.activity_group_position == 0
    assert g1.activity_group_position == 1
    assert g2.activity_group_position == 2
