import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.authorization import admin_role_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.acl import AclBase, AclRead
from app.schemas.general import MessageResponse
from app.services.acl.acl import (
    create_acl_service,
    delete_acl_service,
    get_acl_by_id_service,
    get_all_acls_by_assessment_service,
    get_all_acls_by_user_service,
    get_all_acls_service,
    update_acl_service,
)

router = APIRouter(
    prefix="/acl",
    tags=["acl"],
)


@router.get("/", response_model=list[AclRead])
def get_acls(
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all acls.
    """
    acls = get_all_acls_service(user, session)
    return acls


@router.get("/{acl_id}", response_model=AclRead)
def get_acl(
    acl_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get an acl by ID.
    """
    acl = get_acl_by_id_service(acl_id, user, session)
    return acl


@router.get("/assessment/{assessment_id}", response_model=list[AclRead])
def get_acls_by_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all acls by assessment ID.
    """
    acls = get_all_acls_by_assessment_service(assessment_id, user, session)
    return acls


@router.get("/user/{user_id}", response_model=list[AclRead])
def get_acls_by_user(
    user_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all acls by user ID.
    """
    acls = get_all_acls_by_user_service(user_id, user, session)
    return acls


@router.post("/", response_model=AclRead)
def create_acl(
    acl: AclBase,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Create a new acl.
    """
    acl = create_acl_service(acl, user, session)
    return acl


@router.put("/{acl_id}", response_model=AclRead)
def update_acl(
    acl_id: uuid.UUID,
    acl: AclBase,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Update an acl by ID.
    """
    acl = update_acl_service(acl_id, acl, user, session)
    return acl


@router.delete("/{acl_id}", response_model=MessageResponse)
def delete_acl(
    acl_id: uuid.UUID,
    user: User = Depends(admin_role_validation_service),
    session: Session = Depends(get_session),
):
    """
    Delete an acl by ID.
    """
    delete_acl_service(acl_id, user, session)
    return MessageResponse(message="Acl deleted successfully")
