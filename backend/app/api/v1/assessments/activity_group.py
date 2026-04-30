import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.activity import ActivityRead
from app.schemas.activity_group import (
    ActivityGroupBase,
    ActivityGroupFilter,
    ActivityGroupRead,
    ActivityGroupReorder,
    ActivityReorder,
)
from app.schemas.general import MessageResponse
from app.services.activity_group.activity_group import (
    create_activity_group_service,
    get_activity_group_activities_service,
    get_activity_group_by_id_service,
    get_activity_group_service,
    reorder_activities_service,
    reorder_activity_groups_service,
    toggle_activity_group_delete_service,
    toggle_activity_group_visible_service,
    update_activity_group_service,
)

router = APIRouter(
    prefix="/activity_group",
    tags=["activity_group"],
)


@router.get("/", response_model=list[ActivityGroupRead])
def get_activity_groups(
    assessment_id: uuid.UUID,
    filter_query: Annotated[ActivityGroupFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get all activity groups for an assessment.
    """
    return get_activity_group_service(assessment_id, user, session, filter_query)


@router.get("/{activity_group_id}", response_model=ActivityGroupRead)
def get_activity_group(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get a specific activity group for an assessment.
    """
    return get_activity_group_by_id_service(
        activity_group_id, assessment_id, user, session
    )


@router.get("/{activity_group_id}/activities", response_model=list[ActivityRead])
def get_activity_group_activities(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get all activities for a specific activity group.
    """
    return get_activity_group_activities_service(
        activity_group_id, assessment_id, user, session
    )


@router.post("/", response_model=ActivityGroupRead)
def create_activity_group(
    activity_group: ActivityGroupBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Create a new activity group for an assessment.
    """
    return create_activity_group_service(activity_group, assessment_id, user, session)


@router.put("/reorder", response_model=MessageResponse)
def reorder_activity_groups(
    reorder: ActivityGroupReorder,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Reorder activity groups within an assessment.

    Provide the activity group IDs in the desired order.
    The first ID gets position 0, second gets position 1, etc.
    """
    reorder_activity_groups_service(
        reorder.activity_group_ids, assessment_id, user, session
    )
    return MessageResponse(message="Activity groups reordered successfully")


@router.put("/{activity_group_id}", response_model=ActivityGroupRead)
def update_activity_group(
    activity_group_id: uuid.UUID,
    activity_group: ActivityGroupBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Update an activity group for an assessment.
    """
    return update_activity_group_service(
        activity_group_id, activity_group, assessment_id, user, session
    )


@router.put("/{activity_group_id}/delete", response_model=MessageResponse)
def toggle_activity_group_delete(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Toggle the deleted flag for an activity group for an assessment.
    """
    toggle_activity_group_delete_service(
        activity_group_id, assessment_id, user, session
    )
    return MessageResponse(message="Activity group deleted flag toggled successfully")


@router.put("/{activity_group_id}/visible", response_model=MessageResponse)
def toggle_activity_group_visible(
    activity_group_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Toggle the visible flag for an activity group for an assessment.
    """
    toggle_activity_group_visible_service(
        activity_group_id, assessment_id, user, session
    )
    return MessageResponse(message="Activity group visibility toggled successfully")


@router.put("/{activity_group_id}/reorder", response_model=MessageResponse)
def reorder_activities(
    activity_group_id: uuid.UUID,
    reorder: ActivityReorder,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Reorder activities within an activity group.

    Provide the activity IDs in the desired order.
    The first ID gets position 0, second gets position 1, etc.
    """
    reorder_activities_service(
        activity_group_id, reorder.activity_ids, assessment_id, user, session
    )
    return MessageResponse(message="Activities reordered successfully")
