from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.authentication import (
    get_external_auth_providers_service,
    login_service,
    logout_service,
)
from app.core.config import settings
from app.core.mfa import (
    setup_mfa_service,
    validate_mfa_and_issue_token_service,
    validate_mfa_setup_service,
)
from app.core.token_validation import access_token_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.configuration import ExternalAuthProvider
from app.schemas.general import MessageResponse, MFASetupResponse
from app.schemas.jwt import Token
from app.schemas.otp import OTP

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    """
    Login the user and issue a new token.
    """
    return login_service(form_data.username, form_data.password, session)


@router.post("/logout", response_model=MessageResponse)
def logout(
    user: User = Depends(access_token_validation_service),
    session: Session = Depends(get_session),
):
    """
    Logout the authenticated user.
    """
    logout_service(user, session)
    return MessageResponse(message="Logged out successfully")


@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    user: User = Depends(access_token_validation_service),
    session: Session = Depends(get_session),
):
    """
    Setup MFA for the authenticated user.
    Returns a provisioning URI for QR code generation.
    """
    return setup_mfa_service(user, session)


@router.post("/mfa/setup/validate", response_model=Token)
def validate_mfa_setup(
    otp_data: OTP,
    user: User = Depends(access_token_validation_service),
    session: Session = Depends(get_session),
):
    """
    Validate MFA setup for the authenticated user.
    """
    validate_mfa_setup_service(user, otp_data.otp, session)
    return validate_mfa_and_issue_token_service(user, otp_data.otp)


@router.post("/mfa", response_model=Token)
def validate_mfa(
    otp_data: OTP,
    user: User = Depends(access_token_validation_service),
):
    """
    Validate MFA token and issue a new jwt with MFA verified claim.
    """
    return validate_mfa_and_issue_token_service(user, otp_data.otp)


@router.get("/providers", response_model=list[ExternalAuthProvider])
def get_providers():
    """
    Get a list of available external authentication providers.
    """
    return get_external_auth_providers_service()


@router.get("/motd", response_model=MessageResponse)
def get_motd():
    """
    Get the welcome message of the day.
    """
    return MessageResponse(message=settings.WELCOME_MESSAGE or "")
