from fastapi.testclient import TestClient

from app.models.user import User
from tests.conftest import TEST_ADMIN_EMAIL, TEST_USER_EMAIL, TEST_USER_PASSWORD


def test_get_me_success(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that authenticated user can get their own profile
    """
    response = client.get("/api/v1/user/me", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER_EMAIL
    assert data["role"] == "user"
    assert not data["disabled"]
    assert "id" in data


def test_get_me_admin_user(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that admin user can also get their own profile
    """
    response = client.get("/api/v1/user/me", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_ADMIN_EMAIL
    assert data["role"] == "admin"


def test_get_me_no_auth(client: TestClient, test_regular_user: User):
    """
    Test that unauthenticated request to /me returns 401
    """
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_get_me_invalid_token(client: TestClient, test_regular_user: User):
    """
    Test that request with invalid token returns 401
    """
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401


def test_get_me_malformed_auth_header(client: TestClient, test_regular_user: User):
    """
    Test that request with malformed authorization header returns 401
    """
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": "NotBearer token"}
    )
    assert response.status_code == 401


def test_update_password_success(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that user can successfully update their password
    """
    new_password = "NewPassword123!"
    response = client.put(
        "/api/v1/user/me/password",
        headers=auth_headers_regular,
        json={
            "old_password": TEST_USER_PASSWORD,
            "new_password": new_password,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "success" in data["message"].lower()


def test_update_password_and_login_with_new(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that after password update, user can login with new password
    """
    new_password = "BrandNewPass456!"

    # Update password
    response = client.put(
        "/api/v1/user/me/password",
        headers=auth_headers_regular,
        json={
            "old_password": TEST_USER_PASSWORD,
            "new_password": new_password,
        },
    )
    assert response.status_code == 200

    # Try to login with new password
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_USER_EMAIL,
            "password": new_password,
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data


def test_update_password_wrong_old_password(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that password update fails with incorrect old password
    """
    response = client.put(
        "/api/v1/user/me/password",
        headers=auth_headers_regular,
        json={
            "old_password": "WrongOldPassword123!",
            "new_password": "NewPassword123!",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_update_password_weak_new_password(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that password update fails with weak new password (validation)
    """
    response = client.put(
        "/api/v1/user/me/password",
        headers=auth_headers_regular,
        json={
            "old_password": TEST_USER_PASSWORD,
            "new_password": "weak",  # Too short, no uppercase, no special char
        },
    )
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


def test_update_password_no_auth(client: TestClient, test_regular_user: User):
    """
    Test that unauthenticated password update returns 401
    """
    response = client.put(
        "/api/v1/user/me/password",
        json={
            "old_password": TEST_USER_PASSWORD,
            "new_password": "NewPassword123!",
        },
    )
    assert response.status_code == 401


def test_update_password_invalid_token(client: TestClient, test_regular_user: User):
    """
    Test that password update with invalid token returns 401
    """
    response = client.put(
        "/api/v1/user/me/password",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "old_password": TEST_USER_PASSWORD,
            "new_password": "NewPassword123!",
        },
    )
    assert response.status_code == 401


def test_update_password_missing_fields(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that password update with missing fields returns 422 validation error
    """
    response = client.put(
        "/api/v1/user/me/password",
        headers=auth_headers_regular,
        json={
            "old_password": TEST_USER_PASSWORD,
            # Missing new_password
        },
    )
    assert response.status_code == 422
    assert response.status_code == 422


def test_reset_user_mfa_self_success(
    client: TestClient,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
    session,
):
    """
    Test that user can successfully reset their MFA with correct password
    """
    # Setup auth and MFA for user
    test_regular_user.mfa_secret = "some_secret"
    test_regular_user.mfa_verified = True
    session.commit()
    session.refresh(test_regular_user)

    # Note: In a real integration test with dependency overrides, we might need to
    # ensure the user has the MFA cookie or token if mfa_validation_service is strict.
    # However, mfa_validation_service usually just checks if the user is authenticated
    # and if the session is MFA verified if required.
    # For this endpoint, we're likely using a standard auth token.
    # If mfa_validation_service enforces MFA active, we might need a mocked token.
    # Assuming for this test that the regular auth token is sufficient or we mock the dependency.
    # Let's try with standard auth header first.

    response = client.put(
        "/api/v1/user/me/mfa",
        headers=auth_headers_regular,
        json={"password": TEST_USER_PASSWORD},
    )

    # If the endpoint enforces strict MFA (e.g. user must have logged in with MFA),
    # this might fail with 403 or similar if we haven't simulated a full MFA login.
    # But usually reset endpoints accept a password confirmation as the factor.

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "reset" in data["message"].lower()

    session.refresh(test_regular_user)
    assert test_regular_user.mfa_secret is None


def test_reset_user_mfa_self_wrong_password(
    client: TestClient,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
    session,
):
    """
    Test that MFA reset fails with incorrect password
    """
    # Setup auth and MFA for user
    test_regular_user.mfa_secret = "some_secret"
    test_regular_user.mfa_verified = True
    session.commit()
    session.refresh(test_regular_user)

    response = client.put(
        "/api/v1/user/me/mfa",
        headers=auth_headers_regular,
        json={"password": "WrongPassword123!"},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Incorrect password" in data["detail"]

    session.refresh(test_regular_user)
    assert test_regular_user.mfa_verified is True
