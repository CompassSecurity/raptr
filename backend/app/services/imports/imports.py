import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_group_template import ActivityGroupTemplate
from app.models.activity_template import ActivityTemplate
from app.models.user import User
from app.schemas.activity_group import ActivityGroupBase
from app.services.activity_group.activity_group import (
    create_activity_group_service,
    get_activity_group_by_id_service,
    get_or_create_default_group,
)
from app.services.assessment.assessment import get_assessment_by_id_service
from app.services.campaign_template.campaign_template import (
    get_campaign_template_by_id_service,
)
from app.services.utils.evaluation import (
    calculate_evaluations,
    create_activity_evaluation,
)
from app.services.utils.position import calculate_new_activity_position


def import_from_campaign_template_service(
    campaign_template_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> str:
    """
    Import content from a campaign template into an assessment.
    Creates groups and activities with correct ordering.
    """
    campaign_template = get_campaign_template_by_id_service(
        campaign_template_id, user, session
    )

    group_count = 0
    activity_count = 0

    for item in campaign_template.items:
        if item.item_type == "group" and item.activity_group_template_id:
            import_from_activity_group_templates_service(
                [item.activity_group_template_id],
                assessment_id,
                user,
                session,
            )
            group_count += 1

        elif item.item_type == "activity" and item.activity_template_id:
            # Ungrouped activities go into the default group
            default_group = get_or_create_default_group(
                assessment_id, session, created_by=user.id
            )
            import_from_activity_templates_service(
                [item.activity_template_id],
                assessment_id,
                user,
                session,
                activity_group_id=default_group.id,
            )
            activity_count += 1

    msg = f"Campaign '{campaign_template.name}' imported: {group_count} groups and {activity_count} ungrouped activities."
    return msg


def import_from_activity_group_templates_service(
    activity_group_template_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> int:
    """
    Import multiple activity groups from activity group templates.
    Called from the specific assessment import endpoint.
    """
    get_assessment_by_id_service(assessment_id, user, session)

    activity_group_templates = (
        session.execute(
            select(ActivityGroupTemplate).where(
                ActivityGroupTemplate.id.in_(activity_group_template_ids)
            )
        )
        .scalars()
        .all()
    )

    if len(activity_group_templates) != len(activity_group_template_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more activity group templates not found",
        )

    new_activity_groups = []
    for activity_group_template in activity_group_templates:
        activity_group_data = ActivityGroupBase(name=activity_group_template.name)

        new_activity_group = create_activity_group_service(
            activity_group=activity_group_data,
            assessment_id=assessment_id,
            user=user,
            session=session,
        )
        new_activity_groups.append(new_activity_group)

        # Import activities for this group
        template_ids = [t.id for t in activity_group_template.activity_templates]
        if template_ids:
            import_from_activity_templates_service(
                template_ids,
                assessment_id,
                user,
                session,
                activity_group_id=new_activity_group.id,
            )

    session.commit()

    return len(new_activity_groups)


def import_from_activity_templates_service(
    activity_template_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    activity_group_id: uuid.UUID | None = None,
) -> int:
    """
    Import multiple activities from activity templates to the assessment.
    """
    get_assessment_by_id_service(assessment_id, user, session)

    activity_templates = (
        session.execute(
            select(ActivityTemplate).where(
                ActivityTemplate.id.in_(activity_template_ids)
            )
        )
        .scalars()
        .all()
    )
    if len(activity_templates) != len(activity_template_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more templates not found",
        )

    # Resolve activity group: use default group or specified group
    if activity_group_id is None:
        target_group = get_or_create_default_group(
            assessment_id, session, created_by=user.id
        )
    else:
        target_group = get_activity_group_by_id_service(
            activity_group_id, assessment_id, user, session
        )

    # Calculate start position after existing activities in the target group
    start_position = calculate_new_activity_position(session, target_group.id)

    new_activities = []
    for activity_position_index, activity_template in enumerate(activity_templates):
        new_activity = Activity(
            assessment_id=assessment_id,
            name=activity_template.name,
            mitre_tactic=activity_template.mitre_tactic,
            mitre_technique=activity_template.mitre_technique,
            activity_rationale=activity_template.activity_rationale,
            activity_actions=activity_template.activity_actions,
            activity_requirements=activity_template.activity_requirements,
            activity_notes=activity_template.activity_notes,
            provider=activity_template.provider,
            expected_logging=activity_template.expected_logging,
            expected_prevention=activity_template.expected_prevention,
            expected_alert_creation=activity_template.expected_alert_creation,
            expected_stakeholder_notification=activity_template.expected_stakeholder_notification,
            expected_severity=activity_template.expected_severity,
            priority=activity_template.priority,
            activity_group_id=target_group.id,
            activity_position=start_position + activity_position_index,
            linked_knowledge_base_articles=activity_template.linked_knowledge_base_articles,
            created_by=user.id,
        )
        new_activities.append(new_activity)

    session.add_all(new_activities)
    session.flush()

    for activity in new_activities:
        create_activity_evaluation(activity.id, assessment_id, session)

    session.flush()
    for activity in new_activities:
        session.refresh(activity)
        calculate_evaluations(activity)

    session.commit()

    return len(new_activities)
