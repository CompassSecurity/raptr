import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.enums import UserRole
from app.models.acl import Acl
from app.models.user import User
from app.schemas.acl import AclBase
from app.services.assessment.assessment import get_assessment_by_id_service
from app.services.user.user import get_user_by_id_service


def get_all_acls_service(
    user: User,
    session: Session,
) -> list[Acl]:
    """
    Get all acls.
    """
    statement = select(Acl)
    acls = session.execute(statement).scalars().all()
    return acls


def get_acl_by_id_service(
    acl_id: uuid.UUID,
    user: User,
    session: Session,
) -> Acl:
    """
    Get an acl by ID.
    """
    statement = select(Acl).where(Acl.id == acl_id)
    acl = session.execute(statement).scalar_one_or_none()
    if not acl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Acl not found"
        )
    return acl


def get_all_acls_by_assessment_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> list[Acl]:
    """
    Get all acls by assessment ID.
    """
    get_assessment_by_id_service(assessment_id, user, session)

    statement = select(Acl).where(Acl.assessment_id == assessment_id)
    acls = session.execute(statement).scalars().all()
    return acls


def get_all_acls_by_user_service(
    user_id: uuid.UUID,
    user: User,
    session: Session,
) -> list[Acl]:
    """
    Get all acls by user ID.
    """
    get_user_by_id_service(user_id, user, session)

    statement = select(Acl).where(Acl.user_id == user_id)
    acls = session.execute(statement).scalars().all()
    return acls


def create_acl_service(
    acl: AclBase,
    user: User,
    session: Session,
) -> Acl:
    """
    Create a new acl.
    """
    get_assessment_by_id_service(acl.assessment_id, user, session)

    acl_user_new = get_user_by_id_service(acl.user_id, user, session)
    if acl_user_new.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Admins do not require ACLs"
        )

    statement = select(Acl).where(
        Acl.user_id == acl.user_id, Acl.assessment_id == acl.assessment_id
    )
    db_acl_exists = session.execute(statement).scalar_one_or_none()
    if db_acl_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Acl already exists"
        )

    db_acl_new = Acl(
        user_id=acl.user_id,
        assessment_id=acl.assessment_id,
        assessment_role=acl.assessment_role,
        created_by=user.id,
    )

    session.add(db_acl_new)
    session.commit()
    return db_acl_new


def delete_acl_service(
    acl_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Delete an acl by ID.
    """
    db_acl = get_acl_by_id_service(acl_id, user, session)
    session.delete(db_acl)
    session.commit()


def update_acl_service(
    acl_id: uuid.UUID,
    acl: AclBase,
    user: User,
    session: Session,
) -> Acl:
    """
    Update an acl by ID.
    """
    get_assessment_by_id_service(acl.assessment_id, user, session)

    acl_user = get_user_by_id_service(acl.user_id, user, session)
    if acl_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Admins do not require ACLs"
        )

    db_acl = get_acl_by_id_service(acl_id, user, session)

    statement = select(Acl).where(
        Acl.user_id == acl.user_id, Acl.assessment_id == acl.assessment_id
    )
    db_acl_exists = session.execute(statement).scalar_one_or_none()
    if db_acl_exists and db_acl_exists.id != acl_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Acl already exists"
        )

    db_acl.user_id = acl.user_id
    db_acl.assessment_id = acl.assessment_id
    db_acl.assessment_role = acl.assessment_role
    db_acl.updated_by = user.id
    session.commit()
    return db_acl
