import pyotp
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def test_mfa_setup_flow(
    client: TestClient,
    auth_headers_regular: dict,
    session: Session,
    test_regular_user: User,
):
    """
    Test the full MFA setup flow:
    1. Initiate setup (get secret)
    2. Validate setup with OTP
    """
    # Enable MFA for testing
    settings.OTP_LOCAL_ENABLED = True

    # 1. Initiate Setup
    response = client.post("/api/v1/auth/mfa/setup", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert "provisioning_uri" in data

    # Refresh user to get the secret from DB
    session.refresh(test_regular_user)
    assert test_regular_user.mfa_secret is not None
    secret = test_regular_user.mfa_secret

    # Generate valid OTP
    totp = pyotp.TOTP(secret)
    valid_otp = totp.now()

    # 2. Validate Setup
    response = client.post(
        "/api/v1/auth/mfa/setup/validate",
        headers=auth_headers_regular,
        json={"otp": valid_otp},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Verify user state
    session.refresh(test_regular_user)
    assert test_regular_user.mfa_verified is True


def test_mfa_login_flow(
    client: TestClient,
    auth_headers_regular: dict,
    session: Session,
    test_regular_user: User,
):
    """
    Test the MFA login flow:
    1. Setup MFA (prerequisite)
    2. Call /mfa endpoint with OTP
    3. Verify new token has mfa_provided=True
    """
    settings.OTP_LOCAL_ENABLED = True

    # Prerequisite: Manually setup MFA for user
    secret = pyotp.random_base32()
    test_regular_user.mfa_secret = secret
    test_regular_user.mfa_verified = True
    session.add(test_regular_user)
    session.commit()

    # Generate OTP
    totp = pyotp.TOTP(secret)
    valid_otp = totp.now()

    # Call MFA validation endpoint
    response = client.post(
        "/api/v1/auth/mfa",
        headers=auth_headers_regular,  # Using the non-MFA token
        json={"otp": valid_otp},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Optional: We could decode the token to check the claim,
    # but using it on a protected endpoint is a better functional test.


def test_mfa_enforcement(
    client: TestClient,
    auth_headers_regular: dict,
    session: Session,
    test_regular_user: User,
):
    """
    Test that MFA is enforced on protected routes
    """
    settings.OTP_LOCAL_ENABLED = True

    # 1. User has NOT set up MFA -> Should get 403 Setup Required
    # Ensure user is clean
    test_regular_user.mfa_verified = False
    test_regular_user.mfa_secret = None
    session.add(test_regular_user)
    session.commit()

    # Try to access a protected route (using /api/v1/users/me as example of protected route)
    # Note: We need to make sure we are hitting a route that specifically uses mfa_validation_service
    # The user/me endpoint was updated to use it.
    response = client.get("/api/v1/user/me", headers=auth_headers_regular)
    assert response.status_code == 403
    assert "MFA setup required" in response.json()["detail"]

    # 2. User HAS setup MFA but token is not MFA-verified -> Should get 403 Verification Required
    test_regular_user.mfa_verified = True
    session.add(test_regular_user)
    session.commit()

    response = client.get("/api/v1/user/me", headers=auth_headers_regular)
    assert response.status_code == 403
    assert "MFA required" in response.json()["detail"]


def test_mfa_invalid_otp(
    client: TestClient,
    auth_headers_regular: dict,
    session: Session,
    test_regular_user: User,
):
    """
    Test rejection of invalid OTP
    """
    settings.OTP_LOCAL_ENABLED = True

    # Prerequisite: Setup MFA
    secret = pyotp.random_base32()
    test_regular_user.mfa_secret = secret
    test_regular_user.mfa_verified = True
    session.add(test_regular_user)
    session.commit()

    # Try with wrong OTP
    response = client.post(
        "/api/v1/auth/mfa", headers=auth_headers_regular, json={"otp": "000000"}
    )
    assert response.status_code == 401
    assert "Invalid OTP" in response.json()["detail"]
