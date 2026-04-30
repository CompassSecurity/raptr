import functools
import ssl
from datetime import datetime, timezone

import certifi
import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.authentication import oauth2_scheme
from app.core.config import settings
from app.core.logging import app_logger
from app.db.session import get_session
from app.models.user import User
from app.schemas.configuration import ExternalAuthConfig
from app.services.user.user import get_user_by_email_service


@functools.lru_cache
def get_jwks_client_service(jwks_url: str) -> PyJWKClient:
    """
    Get a PyJWKClient instance for a given JWKS URL.
    Cached to ensure we reuse the same client instance (and its internal key cache).
    Uses certifi for SSL verification to handle environments with missing root certs.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return PyJWKClient(jwks_url, ssl_context=ssl_context)


def validate_external_token_service(
    token: str, issuer: str, config: ExternalAuthConfig
) -> tuple[dict, str]:
    """
    Validate a token from an external issuer using JWKS.
    """
    try:
        jwks_client = get_jwks_client_service(config.jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Prepare validation options
        audience = config.audience

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )

        # Manual validation for azp claim, should be the client_id
        if config.client_id and payload.get("azp") != config.client_id:
            app_logger.error(
                "Token validation failed: Invalid Client ID. Expected %s, got %s",
                config.client_id,
                payload.get("azp"),
            )
            raise InvalidTokenError("Invalid Client ID")

        username = payload.get(config.username_claim)
        if not username:
            raise InvalidTokenError("Username claim missing")

        # Ensure that the IDP only issues tokens for users for which we expect it to issue tokens
        email_domain = username.split("@")[-1]
        if email_domain not in config.trusted_email_domains:
            app_logger.error(
                "Token validation failed: Invalid email domain for this IDP. Expected %s, got %s",
                config.trusted_email_domains,
                email_domain,
            )
            raise InvalidTokenError("Untrusted email domain in token for this IDP")

        return payload, username

    except Exception as e:
        app_logger.error("External token validation failed: %s", str(e))
        raise InvalidTokenError(str(e)) from e


def validate_internal_token_service(token: str) -> tuple[dict, str]:
    """
    Validate a token from the internal issuer using HMAC.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            audience=settings.APPLICATION_NAME,
            issuer=settings.APPLICATION_NAME,
            algorithms=[settings.ALGORITHM],
        )

        username = payload.get("sub")
        if not username:
            raise InvalidTokenError("Username claim missing")

        return payload, username

    except Exception as e:
        app_logger.error("Internal token validation failed: %s", str(e))
        raise InvalidTokenError(str(e)) from e


def validate_user_exists_service(
    username: str, session: Session, payload: dict
) -> User:
    """
    Validate the user exists, is active, and the token is not invalid (e.g. revoked/logout).
    """
    user = get_user_by_email_service(email=username, session=session)

    if user is None:
        app_logger.error("Access token validation failed. User %s not found.", username)
        raise InvalidTokenError("User not found")

    if user.disabled:
        app_logger.error(
            "Access token validation failed. User %s is disabled.", user.email
        )
        raise InvalidTokenError("User is disabled")

    if user.last_logout_at:
        iat_datetime = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        last_logout_at = user.last_logout_at
        if last_logout_at.tzinfo is None:
            last_logout_at = last_logout_at.replace(tzinfo=timezone.utc)

        if last_logout_at >= iat_datetime:
            app_logger.error(
                "Access token validation failed. User %s is logged out.", user.email
            )
            raise InvalidTokenError("User is logged out")

    return user


def access_token_validation_service(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """
    Validate an access token and cache the JWT payload in request state
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract issuer from token (unverified data)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        issuer = unverified_payload.get("iss")

        # Determine validation strategy based on issuer
        external_config = next(
            (
                config
                for config in settings.EXTERNAL_AUTH_CONFIGS
                if config.issuer == issuer
            ),
            None,
        )

        if external_config:
            payload, username = validate_external_token_service(
                token, issuer, external_config
            )
        elif issuer == settings.APPLICATION_NAME:
            payload, username = validate_internal_token_service(token)
        else:
            app_logger.error(
                "Token validation failed: Invalid issuer. Unknown issuer: %s",
                issuer,
            )
            raise InvalidTokenError("Unknown issuer")

        # Validate user
        user = validate_user_exists_service(username, session, payload)

        # Cache JWT payload in request state for use by downstream dependencies
        request.state.jwt_payload = payload

        app_logger.debug("Access token validation successful for user %s.", user.email)
        return user

    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        app_logger.error("Unexpected error during token validation: %s", str(e))
        raise credentials_exception
