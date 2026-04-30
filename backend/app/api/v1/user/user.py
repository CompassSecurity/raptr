from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.general import MessageResponse
from app.schemas.user import UserPasswordMfaReset, UserPasswordUpdate, UserReadAcl
from app.services.acl.acl import get_all_acls_by_user_service
from app.services.user.user import (
    reset_user_mfa_self_service,
    update_user_password_service,
)

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.get("/me", response_model=UserReadAcl)
def read_user_self(
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get the authenticated user, and the corresponding ACLs.
    """
    user.acl = get_all_acls_by_user_service(user.id, user, session)
    return user


@router.put("/me/password", response_model=MessageResponse)
def update_user_password_self(
    user_password_update: UserPasswordUpdate,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Update the authenticated user's password.
    """
    update_user_password_service(user_password_update, user, session)
    return MessageResponse(message="Password updated successfully")


@router.put("/me/mfa", response_model=MessageResponse)
def reset_user_mfa_self(
    password: UserPasswordMfaReset,
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Reset the authenticated user's MFA.
    """
    reset_user_mfa_self_service(password, user, session)
    return MessageResponse(message="MFA reset successfully. Logout to reconfigure MFA.")
