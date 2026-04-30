import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.core.password import hash_password, verify_password
from app.models.user import User
from app.schemas.general import PaginatedResponse
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserFilter,
    UserPasswordMfaReset,
    UserPasswordReset,
    UserPasswordUpdate,
)
from app.services.utils.query import paginated_query


def get_all_users_service(
    user: User,
    session: Session,
    filter_query: UserFilter,
) -> PaginatedResponse[User]:
    """
    Get all users from the database, searchable by user email.
    Returns a PaginatedResponse with users and pagination metadata.
    """
    return paginated_query(session, User, filter_query)


def get_user_by_id_service(
    user_id: uuid.UUID,
    user: User,
    session: Session,
) -> User:
    """
    Get a user by id from the database
    """
    app_logger.debug("Getting user by id: %s", user_id)
    statement = select(User).where(User.id == user_id)
    user = session.execute(statement).scalar_one_or_none()
    if user is None:
        app_logger.debug("User %s not found", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_user_by_email_service(
    email: str,
    session: Session,
) -> User:
    """
    Get a user by email from the database
    """
    app_logger.debug("Getting user by email: %s", email)
    statement = select(User).where(User.email == email)
    user = session.execute(statement).scalar_one_or_none()
    if user is None:
        app_logger.debug("User %s not found", email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def check_user_exists_service(
    email: str,
    session: Session,
) -> bool:
    """
    Check if a user exists in the database
    """
    app_logger.debug("Checking if user %s exists", email)
    statement = select(User).where(User.email == email)
    user = session.execute(statement).scalar_one_or_none()
    if user:
        app_logger.debug("User %s exists", email)
        return True
    app_logger.debug("User %s does not exist", email)
    return False


def create_user_service(
    new_user: UserCreate,
    user: User | None,
    session: Session,
) -> User:
    """
    Create a new user in the database
    """
    app_logger.debug("Creating user: %s", new_user.email)
    if check_user_exists_service(new_user.email, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    hashed_password = hash_password(new_user.password)

    db_user = User(
        email=new_user.email,
        role=new_user.role,
        disabled=new_user.disabled,
        hashed_password=hashed_password,
        mfa_secret=None,
        created_by=user.id if user else None,
    )

    session.add(db_user)
    session.commit()
    app_logger.info("User %s created", db_user.email)
    return db_user


def delete_user_service(
    user_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Delete a user from the database
    """
    app_logger.debug("Deleting user: %s", user_id)
    db_user = get_user_by_id_service(user_id, user, session)
    if db_user.email == settings.ADMIN_EMAIL:
        app_logger.debug("User %s is admin and cannot be deleted", user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete admin user"
        )
    session.delete(db_user)
    session.commit()
    app_logger.info("User %s deleted", user_id)


def update_user_service(
    user_id: uuid.UUID,
    user_update: UserBase,
    user: User,
    session: Session,
) -> User:
    """
    Update a user in the database
    """
    app_logger.debug("Updating user: %s", user_id)

    db_user = get_user_by_id_service(user_id, user, session)

    if db_user.email == settings.ADMIN_EMAIL:
        app_logger.debug("User %s is admin and cannot be updated", user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update admin user"
        )
    if user_update.email != db_user.email and check_user_exists_service(
        user_update.email, session
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    db_user.email = user_update.email
    db_user.role = user_update.role
    db_user.disabled = user_update.disabled
    db_user.updated_by = user.id
    session.commit()
    app_logger.info("User %s updated", db_user.email)
    return db_user


def update_user_password_service(
    user_password_update: UserPasswordUpdate,
    user: User,
    session: Session,
) -> None:
    """
    Update a user's password in the database
    """
    app_logger.debug("Updating user password: %s", user.email)
    db_user = get_user_by_email_service(user.email, session)

    if not verify_password(user_password_update.old_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    new_hashed_password = hash_password(user_password_update.new_password)
    db_user.hashed_password = new_hashed_password
    db_user.updated_by = user.id
    session.commit()
    app_logger.info("User %s password updated", db_user.email)


def reset_user_password_service(
    user_id: uuid.UUID,
    new_password: UserPasswordReset,
    user: User,
    session: Session,
) -> None:
    """
    Reset a user's password in the database
    """
    db_user = get_user_by_id_service(user_id, user, session)
    app_logger.debug("Resetting user password: %s", user_id)

    new_hashed_password = hash_password(new_password.new_password)
    db_user.hashed_password = new_hashed_password
    db_user.updated_by = user.id
    session.commit()
    app_logger.info("User %s password reset", db_user.email)


def reset_user_mfa_service(
    user_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Reset a user's MFA in the database
    """
    app_logger.debug("Resetting user MFA: %s", user_id)
    db_user = get_user_by_id_service(user_id, user, session)

    db_user.mfa_secret = None
    db_user.mfa_verified = False
    db_user.updated_by = user.id
    session.commit()
    app_logger.info("User %s MFA reset", db_user.email)


def reset_user_mfa_self_service(
    password: UserPasswordMfaReset,
    user: User,
    session: Session,
) -> None:
    """
    Reset a user's MFA in the database
    """
    app_logger.debug("Resetting user MFA: %s", user.email)
    db_user = get_user_by_email_service(user.email, session)
    if not verify_password(password.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    db_user.mfa_secret = None
    db_user.mfa_verified = False
    db_user.updated_by = user.id
    session.commit()
    app_logger.info("User %s MFA reset", db_user.email)
