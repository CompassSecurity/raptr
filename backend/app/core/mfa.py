from datetime import timedelta

import pyotp
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.core.token_validation import access_token_validation_service
from app.models.user import User
from app.schemas.general import MFASetupResponse
from app.schemas.jwt import Token


def mfa_validation_service(
    request: Request, user: User = Depends(access_token_validation_service)
) -> User:
    """
    Validate access token and enforce MFA if enabled using cached JWT payload
    """
    is_external = request.state.jwt_payload.get("iss") != settings.APPLICATION_NAME

    if is_external and not settings.OTP_EXTERNAL_ENABLED:
        return user

    if not is_external and not settings.OTP_LOCAL_ENABLED:
        return user

    # Check if user needs to setup MFA
    if not user.mfa_verified:
        app_logger.warning("User %s has not verified MFA yet.", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA setup required. Please visit /api/v1/auth/mfa/setup",
        )

    # Use cached JWT payload from request state (already decoded in access_token_validation_service)
    payload = request.state.jwt_payload
    mfa_provided = payload.get("mfa_provided", False)

    if not mfa_provided:
        app_logger.warning("User %s requires MFA verification.", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA required, visit /api/v1/auth/mfa",
        )

    return user


def generate_otp_service(user: User, session: Session) -> str:
    """
    Generate OTP secret and provisioning URI for user.
    Returns the provisioning URI for QR code generation.
    """
    app_logger.debug("Generating OTP secret for user %s", user.email)

    # Generate a new TOTP secret if user doesn't have one
    if not user.mfa_secret:
        totp_secret = pyotp.random_base32()
        user.mfa_secret = totp_secret
        session.commit()
        app_logger.info("Generated new TOTP secret for user %s", user.email)
    else:
        totp_secret = user.mfa_secret
        app_logger.debug("Using existing TOTP secret for user %s", user.email)

    # Create TOTP instance
    totp = pyotp.TOTP(totp_secret)

    # Generate provisioning URI (for QR code)
    provisioning_uri = totp.provisioning_uri(
        name=user.email, issuer_name=settings.APPLICATION_NAME
    )

    return provisioning_uri


def verify_otp_service(user: User, otp: str) -> bool:
    """
    Verify an OTP code for a user.
    """
    if not user.mfa_secret:
        app_logger.error("User %s does not have MFA secret configured", user.email)
        return False

    totp = pyotp.TOTP(user.mfa_secret)
    is_valid = totp.verify(otp, valid_window=1)

    if is_valid:
        app_logger.info("OTP verification successful for user %s", user.email)
    else:
        app_logger.warning("OTP verification failed for user %s", user.email)

    return is_valid


def setup_mfa_service(user: User, session: Session) -> MFASetupResponse:
    """
    Setup MFA for the authenticated user.
    Checks preconditions and generates provisioning URI.
    """
    if user.mfa_secret and user.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already configured for this user",
        )

    provisioning_uri = generate_otp_service(user, session)

    return MFASetupResponse(
        provisioning_uri=provisioning_uri,
        message="MFA setup initiated. Scan the QR code with your authenticator app.",
    )


def validate_mfa_setup_service(user: User, otp: str, session: Session) -> None:
    """
    Validate MFA setup by verifying the OTP code and marking MFA as verified.
    """
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not configured for this user",
        )

    if user.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already verified for this user",
        )

    if not verify_otp_service(user, otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
        )

    user.mfa_verified = True
    session.commit()


def validate_mfa_and_issue_token_service(user: User, otp: str) -> Token:
    """
    Validate MFA token and issue a new JWT with MFA verified claim.
    """
    from app.core.authentication import create_access_token_service

    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not configured. Please setup MFA first at /mfa/setup",
        )

    if not user.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not validated. Please validate at /mfa/setup/validate",
        )

    if not verify_otp_service(user, otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token_service(
        data={"sub": user.email}, expires_delta=access_token_expires, mfa_provided=True
    )

    return Token(access_token=access_token, token_type="bearer", next_url="/")
