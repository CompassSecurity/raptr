import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import TEST_ADMIN_EMAIL, TEST_USER_EMAIL

# ============================================================================
# LIST USERS - GET /api/v1/admin/users
# ============================================================================


def test_read_users_with_admin_auth(
    client: TestClient,
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can list all users
    """
    response = client.get("/api/v1/admin/users", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 2  # At least admin and regular user
    assert data["total"] >= 2

    emails = [user["email"] for user in data["items"]]
    assert TEST_ADMIN_EMAIL in emails
    assert TEST_USER_EMAIL in emails


def test_read_users_pagination(
    client: TestClient,
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test pagination parameters work correctly
    """
    # Test with limit
    response = client.get("/api/v1/admin/users?limit=1", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["size"] == 1
    assert data["page"] == 1
    assert data["total"] >= 2

    # Test with offset
    response = client.get(
        "/api/v1/admin/users?offset=1&limit=1", headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["size"] == 1
    assert data["page"] == 2  # Second page
    assert data["total"] >= 2


def test_read_users_no_auth(client: TestClient, test_admin_user: User):
    """
    Test that unauthenticated request returns 401
    """
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401


def test_read_users_regular_user_forbidden(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """
    Test that regular user (non-admin) cannot list users
    """
    response = client.get("/api/v1/admin/users", headers=auth_headers_regular)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


# ============================================================================
# GET SINGLE USER - GET /api/v1/admin/users/{user_id}
# ============================================================================


def test_read_user_success(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can get a specific user by ID
    """
    response = client.get(
        f"/api/v1/admin/users/{test_regular_user.id}", headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER_EMAIL
    assert data["role"] == "user"
    assert data["id"] == str(test_regular_user.id)


def test_read_user_not_found(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that requesting non-existent user returns 404
    """
    non_existent_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/admin/users/{non_existent_id}", headers=auth_headers_admin
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_read_user_invalid_uuid(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that invalid UUID format returns 422 validation error
    """
    response = client.get(
        "/api/v1/admin/users/not-a-valid-uuid", headers=auth_headers_admin
    )
    assert response.status_code == 422


def test_read_user_no_auth(client: TestClient, test_regular_user: User):
    """
    Test that unauthenticated request returns 401
    """
    response = client.get(f"/api/v1/admin/users/{test_regular_user.id}")
    assert response.status_code == 401


def test_read_user_regular_user_forbidden(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """
    Test that regular user cannot get other users
    """
    response = client.get(
        f"/api/v1/admin/users/{test_admin_user.id}", headers=auth_headers_regular
    )
    assert response.status_code == 403


# ============================================================================
# CREATE USER - POST /api/v1/admin/users/
# ============================================================================


def test_create_user_success(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that admin can create a new user
    """
    new_user_data = {
        "email": "newuser@test.com",
        "password": "NewUserPass123!",
        "role": "user",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_admin, json=new_user_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_user_data["email"]
    assert data["role"] == new_user_data["role"]
    assert data["disabled"] == new_user_data["disabled"]
    assert "id" in data
    assert "hashed_password" not in data  # Password should not be returned


def test_create_admin_user(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that admin can create another admin user
    """
    new_admin_data = {
        "email": "newadmin@test.com",
        "password": "AdminPass123!",
        "role": "admin",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_admin, json=new_admin_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_admin_data["email"]
    assert data["role"] == "admin"


def test_create_user_duplicate_email(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that creating user with duplicate email fails
    """
    duplicate_user_data = {
        "email": TEST_USER_EMAIL,  # Already exists
        "password": "NewPass123!",
        "role": "user",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_admin, json=duplicate_user_data
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_create_user_weak_password(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that creating user with weak password fails validation
    and does NOT expose the password in the error response
    """
    weak_password_data = {
        "email": "weakpass@test.com",
        "password": "weak",  # Too short, missing requirements
        "role": "user",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_admin, json=weak_password_data
    )
    assert response.status_code == 422

    # Verify password is NOT exposed in error response
    error_data = response.json()
    assert "detail" in error_data

    # Check that password errors have redacted input
    for error in error_data["detail"]:
        if any("password" in str(loc).lower() for loc in error.get("loc", [])):
            assert error.get("input") == "<redacted>", (
                "Password should be redacted in error responses"
            )


def test_create_user_invalid_email(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that creating user with invalid email fails validation
    """
    invalid_email_data = {
        "email": "not-an-email",
        "password": "ValidPass123!",
        "role": "user",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_admin, json=invalid_email_data
    )
    assert response.status_code == 422


def test_create_user_no_auth(client: TestClient):
    """
    Test that unauthenticated user cannot create users
    """
    user_data = {
        "email": "unauthorized@test.com",
        "password": "Pass123!",
        "role": "user",
        "disabled": False,
    }
    response = client.post("/api/v1/admin/users/", json=user_data)
    assert response.status_code == 401


def test_create_user_regular_user_forbidden(
    client: TestClient, test_regular_user: User, auth_headers_regular: dict[str, str]
):
    """
    Test that regular user cannot create users
    """
    user_data = {
        "email": "forbidden@test.com",
        "password": "Pass123!",
        "role": "user",
        "disabled": False,
    }
    response = client.post(
        "/api/v1/admin/users/", headers=auth_headers_regular, json=user_data
    )
    assert response.status_code == 403


# ============================================================================
# UPDATE USER - PUT /api/v1/admin/users/{user_id}
# ============================================================================


def test_update_user_success(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can update a user
    """
    update_data = {"email": "updated@test.com", "role": "user", "disabled": False}
    response = client.put(
        f"/api/v1/admin/users/{test_regular_user.id}",
        headers=auth_headers_admin,
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    assert data["id"] == str(test_regular_user.id)


def test_update_user_partial(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that partial updates work (changing disabled status and email)
    Note: Currently requires changing email due to duplicate check limitation
    """
    update_data = {
        "email": "updated@test.com",
        "role": "user",
        "disabled": True,  # Changing disabled status
    }
    response = client.put(
        f"/api/v1/admin/users/{test_regular_user.id}",
        headers=auth_headers_admin,
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    assert data["disabled"]


def test_update_user_promote_to_admin(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can promote user to admin role
    Note: Currently requires changing email due to duplicate check limitation
    """
    update_data = {
        "email": "updated_admin@test.com",
        "role": "admin",
        "disabled": False,
    }
    response = client.put(
        f"/api/v1/admin/users/{test_regular_user.id}",
        headers=auth_headers_admin,
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"


def test_update_user_not_found(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that updating non-existent user returns 404
    """
    non_existent_id = uuid.uuid4()
    update_data = {"email": "test@test.com", "role": "user", "disabled": False}
    response = client.put(
        f"/api/v1/admin/users/{non_existent_id}",
        headers=auth_headers_admin,
        json=update_data,
    )
    assert response.status_code == 404


def test_update_user_invalid_email(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that updating with invalid email fails validation
    """
    update_data = {"email": "not-valid-email", "role": "user", "disabled": False}
    response = client.put(
        f"/api/v1/admin/users/{test_regular_user.id}",
        headers=auth_headers_admin,
        json=update_data,
    )
    assert response.status_code == 422


def test_update_user_no_auth(client: TestClient, test_regular_user: User):
    """
    Test that unauthenticated request returns 401
    """
    update_data = {"email": "updated@test.com", "role": "user", "disabled": False}
    response = client.put(
        f"/api/v1/admin/users/{test_regular_user.id}", json=update_data
    )
    assert response.status_code == 401


def test_update_user_regular_user_forbidden(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """
    Test that regular user cannot update users
    """
    update_data = {"email": "updated@test.com", "role": "user", "disabled": False}
    response = client.put(
        f"/api/v1/admin/users/{test_admin_user.id}",
        headers=auth_headers_regular,
        json=update_data,
    )
    assert response.status_code == 403


# ============================================================================
# DELETE USER - DELETE /api/v1/admin/users/{user_id}
# ============================================================================


def test_delete_user_success(
    client: TestClient,
    session: Session,
    test_admin_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can delete a user
    """
    # Create a user to delete
    user_to_delete = User(
        email="todelete@test.com", hashed_password="hash", role="user", disabled=False
    )
    session.add(user_to_delete)
    session.commit()
    session.refresh(user_to_delete)
    user_id = user_to_delete.id

    response = client.delete(
        f"/api/v1/admin/users/{user_id}", headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "success" in data["message"].lower()


def test_delete_user_verify_deleted(
    client: TestClient,
    session: Session,
    test_admin_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that deleted user is actually removed from database
    """
    # Create a user to delete
    user_to_delete = User(
        email="verify_deleted@test.com",
        hashed_password="hash",
        role="user",
        disabled=False,
    )
    session.add(user_to_delete)
    session.commit()
    session.refresh(user_to_delete)
    user_id = user_to_delete.id

    # Delete the user
    response = client.delete(
        f"/api/v1/admin/users/{user_id}", headers=auth_headers_admin
    )
    assert response.status_code == 200

    # Verify user is gone
    get_response = client.get(
        f"/api/v1/admin/users/{user_id}", headers=auth_headers_admin
    )
    assert get_response.status_code == 404


def test_delete_user_not_found(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that deleting non-existent user returns 404
    """
    non_existent_id = uuid.uuid4()
    response = client.delete(
        f"/api/v1/admin/users/{non_existent_id}", headers=auth_headers_admin
    )
    assert response.status_code == 404


def test_delete_user_invalid_uuid(
    client: TestClient, test_admin_user: User, auth_headers_admin: dict[str, str]
):
    """
    Test that invalid UUID format returns 422
    """
    response = client.delete(
        "/api/v1/admin/users/not-a-uuid", headers=auth_headers_admin
    )
    assert response.status_code == 422


def test_delete_user_no_auth(client: TestClient, test_regular_user: User):
    """
    Test that unauthenticated request returns 401
    """
    response = client.delete(f"/api/v1/admin/users/{test_regular_user.id}")
    assert response.status_code == 401


def test_delete_user_regular_user_forbidden(
    client: TestClient,
    session: Session,
    test_regular_user: User,
    auth_headers_regular: dict[str, str],
):
    """
    Test that regular user cannot delete users
    """
    # Create a user
    user_to_delete = User(
        email="cantdelete@test.com", hashed_password="hash", role="user", disabled=False
    )
    session.add(user_to_delete)
    session.commit()
    session.refresh(user_to_delete)

    response = client.delete(
        f"/api/v1/admin/users/{user_to_delete.id}", headers=auth_headers_regular
    )
    assert response.status_code == 403


# ============================================================================
# RESET PASSWORD & MFA - POST /api/v1/admin/users/{user_id}/...
# ============================================================================


def test_reset_user_password_endpoint(
    client: TestClient,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can reset a user's password
    """
    new_password = "NewPassword123!"
    reset_data = {"new_password": new_password}

    response = client.post(
        f"/api/v1/admin/users/{test_regular_user.id}/reset_password",
        headers=auth_headers_admin,
        json=reset_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User password reset successfully"

    # Verify login with new password
    login_data = {
        "username": test_regular_user.email,
        "password": new_password,
    }
    login_response = client.post("/api/v1/auth/token", data=login_data)
    assert login_response.status_code == 200


def test_reset_user_mfa_endpoint(
    client: TestClient,
    session: Session,
    test_admin_user: User,
    test_regular_user: User,
    auth_headers_admin: dict[str, str],
):
    """
    Test that admin can reset a user's MFA
    """
    # Enable MFA for user
    test_regular_user.mfa_verified = True
    test_regular_user.mfa_secret = "secret"
    session.commit()
    session.refresh(test_regular_user)

    response = client.post(
        f"/api/v1/admin/users/{test_regular_user.id}/reset_mfa",
        headers=auth_headers_admin,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User MFA reset successfully"

    session.refresh(test_regular_user)
    assert test_regular_user.mfa_verified is False
    assert test_regular_user.mfa_secret is None
