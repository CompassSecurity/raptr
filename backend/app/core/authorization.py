import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import app_logger
from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.enums.enums import AclRole, UserRole
from app.models.acl import Acl
from app.models.user import User
from app.services.assessment.assessment import get_assessment_by_id_service


def admin_role_validation_service(user: User = Depends(mfa_validation_service)) -> User:
    """
    Validate if user has admin role
    """
    if user.role != UserRole.ADMIN.value:
        app_logger.error(
            "User %s tried to perform an admin action but is not an admin", user.email
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return user


def get_role_hierarchy_value(role: AclRole) -> int:
    """
    Return the hierarchy value for a given ACL role.
    spectator (0) < blue (1) < red (2)
    """
    hierarchy = {
        AclRole.SPECTATOR: 0,
        AclRole.BLUE: 1,
        AclRole.RED: 2,
    }
    return hierarchy.get(role, 0)


def require_assessment_role(required_role: AclRole | None = None):
    """
    Dependency factory that creates a validation function for a specific ACL role requirement.
    Returns a dependency that validates if user has the required ACL role for an assessment.

    Args:
        required_role: Minimum required ACL role. If None, only validates access exists.

    Usage:
        @router.get("/path")
        async def my_endpoint(
            user: User = Depends(require_assessment_role(AclRole.RED))
        ):
            ...
    """

    def assessment_access_validation_service(
        assessment_id: uuid.UUID,
        user: User = Depends(mfa_validation_service),
        session: Session = Depends(get_session),
    ) -> User:
        """
        Validate if user has access to assessment with required role
        """
        # Verify assessment exists and user can see it
        get_assessment_by_id_service(assessment_id, user, session)

        # Admins bypass ACL checks
        if user.role == UserRole.ADMIN.value:
            user.assessment_acl_role = AclRole.RED
            return user

        # Query ACL
        statement = select(Acl).where(
            Acl.user_id == user.id, Acl.assessment_id == assessment_id
        )
        acl_db = session.execute(statement).scalar_one_or_none()

        # Check if ACL entry exists (should never occur since we checked access above)
        if not acl_db:
            app_logger.error(
                "User %s does not have access to assessment %s",
                user.email,
                assessment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this assessment",
            )

        # Default to RED if no specific role required
        effective_required_role = (
            required_role if required_role is not None else AclRole.RED
        )

        # Validate role hierarchy
        try:
            user_role = AclRole(acl_db.assessment_role)
        except ValueError:
            app_logger.error(
                "Invalid role %s for user %s on assessment %s",
                acl_db.assessment_role,
                user.email,
                assessment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid role configuration",
            )

        # Check if user's role meets or exceeds required role
        if get_role_hierarchy_value(user_role) < get_role_hierarchy_value(
            effective_required_role
        ):
            app_logger.error(
                "User %s has role %s but requires %s for assessment %s",
                user.email,
                user_role.value,
                effective_required_role.value,
                assessment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {effective_required_role.value}, you have: {user_role.value}",
            )

        # Attach the ACL role to the user object for use in service layer
        user.assessment_acl_role = user_role
        return user

    return assessment_access_validation_service


def validate_activity_update_permission(
    assessment_id: uuid.UUID,
    activity_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
) -> User:
    """
    Validate if user has permission to update an activity.
    Red/Admin: Full access.
    Blue:
        - Activity must be visible
        - Activity must not be deleted
        - Activity state must be 'Waiting Red' or 'Waiting Blue'
        - Can only update specific fields
    """
    # Admin and Red can do anything
    if user.role == UserRole.ADMIN.value or get_role_hierarchy_value(
        user.assessment_acl_role
    ) >= get_role_hierarchy_value(AclRole.RED):
        return user

    # Check Blue permissions
    if user.assessment_acl_role == AclRole.BLUE:
        from app.enums.enums import ActivityState
        from app.models.activity import Activity

        statement = select(Activity).where(
            Activity.id == activity_id, Activity.assessment_id == assessment_id
        )
        db_activity = (
            session.execute(statement).unique().scalar_one_or_none()
        )  # Renamed to db_activity to avoid conflict with arg

        if not db_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
            )

        # Check visibility and deletion
        if not db_activity.visible:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
            )

        if db_activity.deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
            )

        # Check state - Must be waiting for input
        allowed_states = [
            ActivityState.WAITING_RED.value,
            ActivityState.WAITING_BLUE.value,
        ]
        if db_activity.state not in allowed_states:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Activity state must be one of {allowed_states} to be updated by Blue team",
            )

    return user
