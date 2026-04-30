import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authorization import require_assessment_role
from app.db.session import get_session
from app.enums.enums import AclRole
from app.models.user import User
from app.schemas.asset import AssetBase, AssetFilter, AssetRead
from app.schemas.general import MessageResponse, PaginatedResponse
from app.services.asset.asset import (
    create_asset_service,
    get_asset_by_id_service,
    get_assets_service,
    toggle_asset_delete_service,
    update_asset_service,
)

router = APIRouter(
    prefix="/asset",
    tags=["asset"],
)


@router.get("/", response_model=PaginatedResponse[AssetRead])
def get_assets(
    assessment_id: uuid.UUID,
    filter_query: Annotated[AssetFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get all assets for an assessment.
    """
    return get_assets_service(assessment_id, user, session, filter_query)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get a specific asset for an assessment.
    """
    return get_asset_by_id_service(asset_id, assessment_id, user, session)


@router.post("/", response_model=AssetRead)
def create_asset(
    asset: AssetBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Create a new asset for an assessment.
    """
    return create_asset_service(asset, assessment_id, user, session)


@router.put("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: uuid.UUID,
    asset: AssetBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Update a specific asset for an assessment.
    """
    return update_asset_service(asset_id, asset, assessment_id, user, session)


@router.put("/{asset_id}/delete", response_model=MessageResponse)
def toggle_asset_delete(
    asset_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Toggle the deleted flag for a specific asset for an assessment.
    """
    toggle_asset_delete_service(asset_id, assessment_id, user, session)
    return MessageResponse(message="Asset deleted flag toggled successfully")
