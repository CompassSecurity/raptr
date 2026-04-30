import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.enums import AclRole
from app.models.activity import Activity
from app.models.activity_group import ActivityGroup
from app.models.user import User
from app.schemas.activity_group import ActivityGroupBase, ActivityGroupFilter
from app.services.activity.activity import get_activity_by_id_service
from app.services.utils.position import (
    calculate_new_activity_position,
    calculate_new_position,
)
from app.services.utils.query import query


def get_or_create_default_group(
    assessment_id: uuid.UUID,
    session: Session,
    created_by: uuid.UUID | None = None,
) -> ActivityGroup:
    """
    Get the default activity group for an assessment, creating it if it doesn't exist.
    Uses flush() so the caller controls the transaction boundary.
    """
    group = session.execute(
        select(ActivityGroup).where(
            ActivityGroup.assessment_id == assessment_id,
            ActivityGroup.is_default.is_(True),
        )
    ).scalar_one_or_none()
    if group is None:
        group = ActivityGroup(
            assessment_id=assessment_id,
            name="Ungrouped",
            visible=True,
            is_default=True,
            created_by=created_by,
        )
        session.add(group)
        session.flush()
    return group


def get_activity_group_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: ActivityGroupFilter,
) -> list[ActivityGroup]:
    """
    Get activity groups for an assessment. Searchable by name.
    """
    statement = select(ActivityGroup).where(
        ActivityGroup.assessment_id == assessment_id
    )

    if user.assessment_acl_role != AclRole.RED:
        statement = statement.where(ActivityGroup.visible).where(
            ActivityGroup.deleted.is_(False)
        )

    return query(session, ActivityGroup, filter_query, statement)


def get_activity_group_by_id_service(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityGroup:
    """
    Get a specific activity group for an assessment.
    """
    statement = select(ActivityGroup).where(
        ActivityGroup.assessment_id == assessment_id,
        ActivityGroup.id == activity_group_id,
    )
    if user.assessment_acl_role != AclRole.RED:
        statement = statement.where(ActivityGroup.visible).where(
            ActivityGroup.deleted.is_(False)
        )
    activitygroup = session.execute(statement).scalar_one_or_none()
    if not activitygroup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity group not found"
        )
    return activitygroup


def get_activity_group_activities_service(
    activity_group_id: uuid.UUID, assessment_id: uuid.UUID, user: User, session: Session
) -> list[Activity]:
    """
    Get all activities for a specific activity group.
    """
    get_activity_group_by_id_service(activity_group_id, assessment_id, user, session)

    statement = select(Activity).where(Activity.activity_group_id == activity_group_id)
    if user.assessment_acl_role != AclRole.RED:
        statement = statement.where(Activity.visible).where(Activity.deleted.is_(False))
    activities = session.execute(statement).scalars().unique().all()
    return activities


def create_activity_group_service(
    activity_group: ActivityGroupBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityGroup:
    """
    Create a new activity group
    """
    # Calculate position at end of list
    new_position = calculate_new_position(
        session,
        ActivityGroup.activity_group_position,
        [ActivityGroup.assessment_id == assessment_id],
    )

    activitygroup = ActivityGroup(
        assessment_id=assessment_id,
        name=activity_group.name,
        created_by=user.id,
        activity_group_position=new_position,
    )
    session.add(activitygroup)
    session.commit()
    return activitygroup


def update_activity_group_service(
    activity_group_id: uuid.UUID,
    activity_group: ActivityGroupBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> ActivityGroup:
    """
    Update an activity group
    """
    activity_group_db = get_activity_group_by_id_service(
        activity_group_id, assessment_id, user, session
    )
    activity_group_db.name = activity_group.name
    activity_group_db.visible = activity_group.visible
    activity_group_db.updated_by = user.id
    session.add(activity_group_db)
    session.commit()
    return activity_group_db


def toggle_activity_group_delete_service(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Toggle the deleted flag for an activity group
    """
    activitygroup = get_activity_group_by_id_service(
        activity_group_id, assessment_id, user, session
    )
    if activitygroup.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default activity group",
        )
    if activitygroup.deleted:
        # Restore group and all its activities
        activitygroup.deleted = False
        activitygroup.deleted_by = None
        activitygroup.deleted_at = None

        for activity in activitygroup.activities:
            activity.deleted = False
            activity.deleted_by = None
            activity.deleted_at = None
            session.add(activity)

    else:
        # Delete group and all its activities
        activitygroup.deleted = True
        activitygroup.deleted_by = user.id
        activitygroup.deleted_at = func.now()

        for activity in activitygroup.activities:
            activity.deleted = True
            activity.deleted_by = user.id
            activity.deleted_at = func.now()
            session.add(activity)

    session.add(activitygroup)
    session.commit()


def toggle_activity_group_visible_service(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Toggle the visible flag for an activity group
    """
    activitygroup = get_activity_group_by_id_service(
        activity_group_id, assessment_id, user, session
    )

    if activitygroup.visible:
        activitygroup.visible = False
        activitygroup.updated_by = user.id
    else:
        activitygroup.visible = True
        activitygroup.updated_by = user.id

    session.add(activitygroup)
    session.commit()


def reorder_activity_groups_service(
    ordered_activity_group_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Reorder activity groups within an assessment.
    """
    from app.services.assessment.assessment import get_assessment_by_id_service

    # Validate assessment
    get_assessment_by_id_service(assessment_id, user, session)

    # Get all non-deleted activity groups for the assessment
    statement = select(ActivityGroup).where(
        ActivityGroup.assessment_id == assessment_id,
        ActivityGroup.deleted.is_(False),
    )
    all_groups = session.execute(statement).scalars().all()
    all_group_ids = {g.id for g in all_groups}

    # Validate provided IDs
    provided_ids = set(ordered_activity_group_ids)
    if provided_ids != all_group_ids:
        missing = all_group_ids - provided_ids
        extra = provided_ids - all_group_ids
        error_msg = "Invalid activity group IDs for reordering."
        if missing:
            error_msg += f" Missing: {missing}."
        if extra:
            error_msg += f" Extra: {extra}."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Update positions and recalculate activity positions for affected groups
    group_map = {g.id: g for g in all_groups}
    for index, group_id in enumerate(ordered_activity_group_ids):
        group = group_map[group_id]
        group.activity_group_position = index
        session.add(group)

        session.add(group)

    session.commit()


def reorder_activities_service(
    activity_group_id: uuid.UUID,
    ordered_activity_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Reorder activities within an activity group.
    All non-deleted activities in the group must be included to prevent position conflicts.
    """
    # Validate group exists and belongs to assessment
    get_activity_group_by_id_service(activity_group_id, assessment_id, user, session)

    # Get ALL non-deleted activities in the group
    all_activities_statement = select(Activity).where(
        Activity.activity_group_id == activity_group_id, Activity.deleted.is_(False)
    )
    all_group_activities = (
        session.execute(all_activities_statement).scalars().unique().all()
    )
    all_activity_ids = {a.id for a in all_group_activities}

    # Check if the provided IDs match the actual group activities
    provided_ids = set(ordered_activity_ids)
    if provided_ids != all_activity_ids:
        missing_ids = all_activity_ids - provided_ids
        extra_ids = provided_ids - all_activity_ids

        error_parts = []
        if missing_ids:
            error_parts.append(f"Missing activities from group: {missing_ids}")
        if extra_ids:
            error_parts.append(f"Invalid activity IDs (not in group): {extra_ids}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All activities in group must be included. {', '.join(error_parts)}",
        )

    # Create lookup map for O(1) access
    activity_map = {a.id: a for a in all_group_activities}

    # Update positions based on new order
    for index, activity_id in enumerate(ordered_activity_ids):
        activity = activity_map[activity_id]
        activity.activity_position = index
        session.add(activity)

    session.commit()


def assign_activity_to_activity_group_service(
    activity_id: uuid.UUID,
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Activity:
    """
    Assign an activity to a group and automatically calculate its position.
    Validates the group exists and belongs to the same assessment as the activity.
    """
    # Validate group exists and belongs to assessment
    get_activity_group_by_id_service(activity_group_id, assessment_id, user, session)

    # Get activity and validate it exists
    activity = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Validate activity belongs to the same assessment as the group
    if activity.assessment_id != assessment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity does not belong to this assessment",
        )

    # Calculate position at end of group
    new_position = calculate_new_activity_position(session, activity_group_id)

    # Assign activity to group
    activity.activity_group_id = activity_group_id
    activity.activity_position = new_position

    session.add(activity)
    session.commit()
    return activity


def remove_activity_from_activity_group_service(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Activity:
    """
    Remove an activity from its group and move it to the default group.
    Reorders remaining activities in the old group to fill the gap.
    """
    # Get activity and validate it exists
    activity = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Get default group
    default_group = get_or_create_default_group(
        assessment_id, session, created_by=user.id
    )

    # Store old group info before moving
    old_group_id = activity.activity_group_id
    old_position = activity.activity_position

    # If already in default group, nothing to do
    if old_group_id == default_group.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity is already in the default group",
        )

    # Calculate position at end of default group
    new_position = calculate_new_activity_position(session, default_group.id)

    # Move to default group
    activity.activity_group_id = default_group.id
    activity.activity_position = new_position
    session.add(activity)

    # Reorder remaining activities in the group to fill the gap
    if old_group_id is not None:
        # Get all activities in the group that were after the removed activity
        activities_to_reorder = (
            session.execute(
                select(Activity).where(
                    Activity.activity_group_id == old_group_id,
                    Activity.activity_position > old_position,
                    Activity.deleted.is_(False),
                )
            )
            .unique()
            .scalars()
            .all()
        )

        # Decrement their positions by 1
        for act in activities_to_reorder:
            act.activity_position -= 1
            session.add(act)

    session.commit()
    return activity
