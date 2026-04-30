import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import admin_role_validation_service
from app.core.config import settings
from app.db.session import get_session
from app.models.user import User
from app.schemas.configuration import Configuration
from app.schemas.general import MessageResponse, PaginatedResponse
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserFilter,
    UserPasswordReset,
    UserRead,
)
from app.services.seed.art import import_atomic_red_team_activity_templates_service
from app.services.seed.custom_data import import_custom_data_service
from app.services.seed.mitre import (
    download_mitre_data,
    parse_and_ingest_mitre_data_service,
)
from app.services.user.user import (
    create_user_service,
    delete_user_service,
    get_all_users_service,
    get_user_by_id_service,
    reset_user_mfa_service,
    reset_user_password_service,
    update_user_service,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/users", response_model=PaginatedResponse[UserRead])
def read_users(
    filter_query: Annotated[UserFilter, Query()],
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all users with pagination metadata.
    """
    return get_all_users_service(user, session, filter_query)


@router.get("/users/{user_id}", response_model=UserRead)
def read_user(
    user_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get a user by ID.
    """
    user = get_user_by_id_service(user_id, user, session)
    return user


@router.post("/users/", response_model=UserRead)
def create_user(
    new_user: UserCreate,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Create a new user.
    """
    return create_user_service(new_user, user, session)


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    user_update: UserBase,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Update a user by ID.
    """
    return update_user_service(user_id, user_update, user, session)


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Delete a user by ID.
    """
    delete_user_service(user_id, user, session)
    return MessageResponse(message="User deleted successfully")


@router.post("/users/{user_id}/reset_password", response_model=MessageResponse)
def reset_user_password(
    user_id: uuid.UUID,
    new_password: UserPasswordReset,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Reset a user's password.
    """
    reset_user_password_service(user_id, new_password, user, session)
    return MessageResponse(message="User password reset successfully")


@router.post("/users/{user_id}/reset_mfa", response_model=MessageResponse)
def reset_user_mfa(
    user_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Reset a user's MFA.
    """
    reset_user_mfa_service(user_id, user, session)
    return MessageResponse(message="User MFA reset successfully")


@router.post("/seed/mitre/", response_model=MessageResponse)
async def import_mitre_techniques_and_tactics(
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Create MITRE ATT&CK data.
    """
    parse_and_ingest_mitre_data_service(session, await download_mitre_data())
    return MessageResponse(message="MITRE ATT&CK data created successfully")


@router.post("/seed/custom", response_model=MessageResponse)
def import_custom_data(
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Import custom data from git repository.
    """
    msg = import_custom_data_service(user, session)
    return MessageResponse(message=msg)


@router.post("/seed/ART", response_model=MessageResponse)
def import_atomic_red_team_activity_templates(
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Import Atomic Red Team templates from git repository.
    """
    msg = import_atomic_red_team_activity_templates_service(user, session)
    return MessageResponse(message=msg)


@router.get("/configuration", response_model=Configuration)
def get_configuration(
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get the configuration of the server.
    """
    return settings
