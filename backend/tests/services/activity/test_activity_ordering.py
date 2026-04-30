from datetime import datetime

from sqlalchemy.orm import Session

from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.activity import ActivityBase
from app.services.activity.activity import create_activity_service
from app.services.activity_group.activity_group import (
    assign_activity_to_activity_group_service,
    reorder_activities_service,
)


def test_activity_ordering_service(session: Session, test_regular_user: User):
    # Add ACL role attribute to user (normally set by API dependency)
    from app.enums.enums import AclRole

    test_regular_user.assessment_acl_role = AclRole.RED

    # 1. Setup Assessment
    assessment = Assessment(
        name="Test Assessment",
        description="Test Description",
        assessment_type="PurpleTeam",
        created_by=test_regular_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)

    # 2. Setup Activity Group
    group = ActivityGroup(
        name="Test Group", assessment_id=assessment.id, created_by=test_regular_user.id
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    # 3. Create Activities (without group assignment)
    activity_data_base = {
        "name": "Activity 1",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1",
        "provider": "Test",
        "priority": "Low",
        "visible": True,
        "state": "Pending",
        "activity_rationale": "Test",
        "activity_actions": "Test",
        "activity_requirements": "Test",
        "activity_notes": "Test",
        "activity_sources": "Test",
        "activity_targets": "Test",
        "activity_tools": "Test",
        "activity_start_time": datetime(2023, 1, 1, 0, 0, 0),
        "activity_end_time": datetime(2023, 1, 1, 1, 0, 0),
        "expected_prevention": False,
        "expected_alert_creation": False,
        "expected_severity": "Low",
        "expected_incident_creation": False,
        "logged": False,
        "prevented": False,
        "prevent_time": datetime(2023, 1, 1, 0, 0, 0),
        "prevention_sources": "",
        "alerted": False,
        "alert_severity": "Low",
        "alert_time": datetime(2023, 1, 1, 0, 0, 0),
        "alert_sources": "",
        "incident_created": False,
        "incident_severity": "Low",
        "incident_time": datetime(2023, 1, 1, 0, 0, 0),
        "incident_sources": "",
        "expected_logging": False,
        "expected_stakeholder_notification": False,
        "stakeholder_notification_created": False,
        "stakeholder_notification_severity": "Low",
        "log_notes": "",
        "alert_notes": "",
        "prevent_notes": "",
        "stakeholder_notification_notes": "",
    }

    # Create Activity A
    act1_data = activity_data_base.copy()
    act1_data["name"] = "Activity A"
    act1 = create_activity_service(
        ActivityBase(**act1_data), assessment.id, test_regular_user, session
    )
    # Assign to group
    act1 = assign_activity_to_activity_group_service(
        act1.id, group.id, assessment.id, test_regular_user, session
    )
    # New positions should be 0-indexed per group
    assert act1.activity_position == 0

    # Create Activity B
    act2_data = activity_data_base.copy()
    act2_data["name"] = "Activity B"
    act2 = create_activity_service(
        ActivityBase(**act2_data), assessment.id, test_regular_user, session
    )
    # Assign to group
    act2 = assign_activity_to_activity_group_service(
        act2.id, group.id, assessment.id, test_regular_user, session
    )
    assert act2.activity_position == 1

    # Create Activity C
    act3_data = activity_data_base.copy()
    act3_data["name"] = "Activity C"
    act3 = create_activity_service(
        ActivityBase(**act3_data), assessment.id, test_regular_user, session
    )
    # Assign to group
    act3 = assign_activity_to_activity_group_service(
        act3.id, group.id, assessment.id, test_regular_user, session
    )
    assert act3.activity_position == 2

    # Verify default order in group
    session.refresh(group)
    assert group.activities[0].id == act1.id
    assert group.activities[1].id == act2.id
    assert group.activities[2].id == act3.id

    # 4. Reorder: C, A, B
    new_order = [act3.id, act1.id, act2.id]
    reorder_activities_service(
        group.id, new_order, assessment.id, test_regular_user, session
    )

    session.refresh(act1)
    session.refresh(act2)
    session.refresh(act3)
    session.expire(group, ["activities"])
    session.refresh(group)

    # Verify positions (0-indexed)
    assert act3.activity_position == 0
    assert act1.activity_position == 1
    assert act2.activity_position == 2

    # Verify group order
    assert group.activities[0].id == act3.id
    assert group.activities[1].id == act1.id
    assert group.activities[2].id == act2.id
