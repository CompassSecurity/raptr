import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.general import MessageResponse, PaginatedResponse
from app.schemas.tag import TagBase, TagFilter, TagRead
from app.services.tag.tag import (
    create_tag_service,
    get_tag_by_id_service,
    get_tags_service,
    toggle_tag_delete_service,
    update_tag_service,
)

router = APIRouter(
    prefix="/tag",
    tags=["tag"],
)


@router.get("/", response_model=PaginatedResponse[TagRead])
def get_tags(
    assessment_id: uuid.UUID,
    filter_query: Annotated[TagFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get all tags for an assessment.
    """
    return get_tags_service(assessment_id, user, session, filter_query)


@router.get("/{tag_id}", response_model=TagRead)
def get_tag(
    tag_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get a specific tag for an assessment.
    """
    return get_tag_by_id_service(tag_id, assessment_id, user, session)


@router.post("/", response_model=TagRead)
def create_tag(
    tag: TagBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Create a new tag for an assessment.
    """
    return create_tag_service(tag, assessment_id, user, session)


@router.put("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: uuid.UUID,
    tag: TagBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Update a specific tag for an assessment.
    """
    return update_tag_service(tag_id, tag, assessment_id, user, session)


@router.put("/{tag_id}/delete", response_model=MessageResponse)
def toggle_tag_delete(
    tag_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Toggle the deleted flag for a specific tag for an assessment.
    """
    toggle_tag_delete_service(tag_id, assessment_id, user, session)
    return MessageResponse(message="Tag deleted flag toggled successfully")
