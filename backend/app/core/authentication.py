from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.core.password import verify_password
from app.models.user import User
from app.schemas.configuration import ExternalAuthProvider
from app.schemas.jwt import Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def login_service(
    username: str,
    password: str,
    session: Session,
) -> Token:
    """
    Authenticate user, track login, create access token, and determine next URL.
    """
    user = authenticate_user_service(username, password, session)
    update_last_login_service(user, session)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token_service(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    if settings.OTP_LOCAL_ENABLED:
        next_url = "/mfa" if user.mfa_verified else "/mfa/setup"
    else:
        next_url = "/"

    return Token(access_token=access_token, token_type="bearer", next_url=next_url)


def authenticate_user_service(
    username: str,
    password: str,
    session: Session,
) -> User:
    """
    Authenticate user login credentials and if user is disabled
    """
    statement = select(User).where(User.email == username)
    user = session.execute(statement).scalar_one_or_none()

    if not user:
        app_logger.error(
            "Login attempt with user %s failed. Incorrect username.", username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(password, user.hashed_password):
        app_logger.error(
            "Login attempt with user %s failed. Incorrect password.", username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if user.disabled:
        app_logger.error(
            "Login attempt with user %s failed. User is disabled.", username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is disabled"
        )

    app_logger.debug("Login attempt with user %s successful.", username)
    return user


def update_last_login_service(user: User, session: Session) -> None:
    """
    Update user's last login timestamp
    """
    app_logger.debug("Updating last login for user %s", user.email)
    user.last_login_at = datetime.now(timezone.utc)
    session.commit()


def create_access_token_service(
    data: dict,
    expires_delta: timedelta | None = None,
    mfa_provided: bool = False,
) -> str:
    """
    Create an access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"iss": settings.APPLICATION_NAME})
    to_encode.update({"aud": settings.APPLICATION_NAME})
    to_encode.update({"iat": datetime.now(timezone.utc)})
    to_encode.update({"exp": expire})
    to_encode.update({"mfa_provided": mfa_provided})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def logout_service(user: User, session: Session) -> None:
    """
    Logout a user
    """
    app_logger.debug("Logging out user %s", user.email)
    user.last_logout_at = datetime.now(timezone.utc)
    session.commit()
    app_logger.info("User %s logged out", user.email)


def get_external_auth_providers_service() -> list[ExternalAuthProvider]:
    """
    Return configured external authentication providers.
    """
    return [
        ExternalAuthProvider(
            name=config.name,
            authority=config.issuer,
            client_id=config.client_id,
            scope=config.scope,
        )
        for config in settings.EXTERNAL_AUTH_CONFIGS
    ]
