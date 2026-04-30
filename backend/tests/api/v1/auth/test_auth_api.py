from fastapi.testclient import TestClient

from app.models.user import User
from tests.conftest import (
    TEST_ADMIN_EMAIL,
    TEST_ADMIN_PASSWORD,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)


def test_login_success_admin(client: TestClient, test_admin_user: User):
    """
    Test successful login with valid admin credentials returns access token
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_success_regular_user(client: TestClient, test_regular_user: User):
    """
    Test successful login with valid regular user credentials returns access token
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_username(client: TestClient, test_admin_user: User):
    """
    Test login with non-existent username returns 401 Unauthorized
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "nonexistent@test.com",
            "password": TEST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "username or password" in data["detail"].lower()


def test_login_invalid_password(client: TestClient, test_admin_user: User):
    """
    Test login with incorrect password returns 401 Unauthorized
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_ADMIN_EMAIL,
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "username or password" in data["detail"].lower()


def test_login_disabled_user(client: TestClient, test_disabled_user: User):
    """
    Test login with disabled user returns 401 Unauthorized
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": test_disabled_user.email,
            "password": "DisabledPass123!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "disabled" in data["detail"].lower()


def test_login_missing_credentials(client: TestClient):
    """
    Test login with missing credentials returns 422 Validation Error
    """
    response = client.post(
        "/api/v1/auth/token",
        data={},
    )
    assert response.status_code == 422


def test_token_format(client: TestClient, test_admin_user: User):
    """
    Test that returned token is a valid JWT format (three parts separated by dots)
    """
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # JWT tokens have 3 parts separated by periods
    token_parts = token.split(".")
    assert len(token_parts) == 3

    # Each part should be non-empty
    assert all(len(part) > 0 for part in token_parts)


def test_login_form_data_content_type(client: TestClient, test_admin_user: User):
    """
    Test that login endpoint accepts form data (OAuth2 spec requirement)
    """
    # This should work with form data content type
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200


def test_token_invalidation_after_logout(client: TestClient, test_admin_user: User):
    """
    Test that a token is invalidated after the user logs out
    """
    # 1. Login to get a valid token
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify token works by hitting a protected endpoint
    response = client.get("/api/v1/user/me", headers=headers)

    assert response.status_code == 200

    # 3. Logout using the token
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200

    # 4. Try to use the same token again - should be unauthorized
    response = client.get("/api/v1/user/me", headers=headers)
    assert response.status_code == 401
