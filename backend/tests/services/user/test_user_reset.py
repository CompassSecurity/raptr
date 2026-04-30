import uuid

import pytest
from fastapi import HTTPException

from app.core.password import hash_password
from app.models.user import User
from app.schemas.user import UserPasswordReset
from app.services.user.user import (
    reset_user_mfa_service,
    reset_user_password_service,
)


@pytest.fixture
def test_regular_user(session, test_admin_user):
    user = User(
        email="regular@test.com",
        role="user",
        disabled=False,
        hashed_password=hash_password("OldPassword123!"),
        mfa_secret="testsecret",
        mfa_verified=True,
        created_by=test_admin_user.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_reset_user_password(session, test_admin_user, test_regular_user):
    new_password = UserPasswordReset(new_password="NewPassword123!")

    result = reset_user_password_service(
        test_regular_user.id, new_password, test_admin_user, session
    )

    assert result is None

    # Verify password was changed
    session.refresh(test_regular_user)
    from app.core.password import verify_password

    assert verify_password("NewPassword123!", test_regular_user.hashed_password)


def test_reset_user_password_user_not_found(session, test_admin_user):
    new_password = UserPasswordReset(new_password="NewPassword123!")

    with pytest.raises(HTTPException) as exc:
        reset_user_password_service(
            uuid.uuid4(), new_password, test_admin_user, session
        )
    assert exc.value.status_code == 404


def test_reset_user_mfa(session, test_admin_user, test_regular_user):
    # Verify MFA is currently set
    assert test_regular_user.mfa_secret is not None
    assert test_regular_user.mfa_verified is True

    result = reset_user_mfa_service(test_regular_user.id, test_admin_user, session)

    assert result is None

    # Verify MFA was reset
    session.refresh(test_regular_user)
    assert test_regular_user.mfa_secret is None
    assert test_regular_user.mfa_verified is False


def test_reset_user_mfa_user_not_found(session, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        reset_user_mfa_service(uuid.uuid4(), test_admin_user, session)
    assert exc.value.status_code == 404
