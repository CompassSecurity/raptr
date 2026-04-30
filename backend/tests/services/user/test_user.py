import pytest
from fastapi import HTTPException

from app.core.password import verify_password
from app.schemas.user import UserPasswordMfaReset, UserPasswordReset
from app.services.user.user import (
    reset_user_mfa_self_service,
    reset_user_mfa_service,
    reset_user_password_service,
)
from tests.conftest import TEST_USER_PASSWORD


def test_reset_user_password_service(session, test_regular_user):
    new_password_str = "NewPassword123!"
    reset_data = UserPasswordReset(new_password=new_password_str)

    result = reset_user_password_service(
        test_regular_user.id, reset_data, test_regular_user, session
    )

    assert result is None
    session.refresh(test_regular_user)
    assert verify_password(new_password_str, test_regular_user.hashed_password)


def test_reset_user_mfa_service(session, test_regular_user):
    # Setup user with MFA
    test_regular_user.mfa_secret = "some_secret"
    test_regular_user.mfa_verified = True
    session.commit()
    session.refresh(test_regular_user)

    reset_user_mfa_service(test_regular_user.id, test_regular_user, session)

    assert test_regular_user.mfa_verified is False


def test_reset_user_mfa_self_service_success(session, test_regular_user):
    # Setup user with MFA
    test_regular_user.mfa_secret = "some_secret"
    test_regular_user.mfa_verified = True
    session.commit()
    session.refresh(test_regular_user)

    password_data = UserPasswordMfaReset(password=TEST_USER_PASSWORD)
    reset_user_mfa_self_service(password_data, test_regular_user, session)

    assert test_regular_user.mfa_verified is False


def test_reset_user_mfa_self_service_wrong_password(session, test_regular_user):
    # Setup user with MFA
    test_regular_user.mfa_secret = "some_secret"
    test_regular_user.mfa_verified = True
    session.commit()
    session.refresh(test_regular_user)

    password_data = UserPasswordMfaReset(password="WrongPassword123!")

    with pytest.raises(HTTPException) as excinfo:
        reset_user_mfa_self_service(password_data, test_regular_user, session)

    assert excinfo.value.status_code == 400
    assert "Incorrect password" in excinfo.value.detail

    # Verify MFA is still enabled
    session.refresh(test_regular_user)
    assert test_regular_user.mfa_secret == "some_secret"
    assert test_regular_user.mfa_verified is True
    assert test_regular_user.mfa_verified is True
