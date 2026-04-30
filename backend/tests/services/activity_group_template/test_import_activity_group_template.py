import pytest
from sqlalchemy import select

from app.models.activity import Activity
from app.models.activity_group import ActivityGroup
from app.models.activity_group_template import ActivityGroupTemplate
from app.models.activity_template import ActivityTemplate
from app.models.assessment import Assessment
from app.services.imports.imports import (
    import_from_activity_group_templates_service,
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


def test_import_activity_group_templates(session, test_assessment, test_admin_user):
    # 1. Create Data
    # Create Activity Templates
    a1 = ActivityTemplate(
        name="Activity 1",
        mitre_tactic="Tactic 1",
        mitre_technique="T1",
        provider="Test",
        created_by=test_admin_user.id,
    )
    a2 = ActivityTemplate(
        name="Activity 2",
        mitre_tactic="Tactic 1",
        mitre_technique="T1",
        provider="Test",
        created_by=test_admin_user.id,
    )
    session.add_all([a1, a2])
    session.flush()

    # Create Group Template
    gt = ActivityGroupTemplate(name="Group Template 1")
    gt.activity_templates.append(a1)
    gt.activity_templates.append(a2)
    session.add(gt)
    session.commit()

    # 2. Call Service
    import_from_activity_group_templates_service(
        [gt.id], test_assessment.id, test_admin_user, session
    )

    # 3. Verify
    # Check Group Created
    groups = (
        session.execute(
            select(ActivityGroup).where(
                ActivityGroup.assessment_id == test_assessment.id
            )
        )
        .scalars()
        .all()
    )
    assert len(groups) == 1
    group = groups[0]
    assert group.name == "Group Template 1"

    # Check Activities Created
    activities = (
        session.execute(
            select(Activity).where(Activity.assessment_id == test_assessment.id)
        )
        .unique()
        .scalars()
        .all()
    )
    assert len(activities) == 2

    # Check Association
    # Activities should belong to the group
    activity_names = sorted([a.name for a in activities])
    assert activity_names == ["Activity 1", "Activity 2"]

    assert activities[0].activity_group_id == group.id
    assert activities[1].activity_group_id == group.id

    # Check unique positions (0-indexed now)
    positions = [a.activity_position for a in activities]
    assert len(set(positions)) == 2  # All positions are unique
    assert 0 in positions
    assert 1 in positions
