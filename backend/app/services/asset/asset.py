import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.enums.enums import AclRole, ActivityAssetRole
from app.models.activity import activity_asset_association
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetBase, AssetFilter, AssetRead
from app.schemas.general import PaginatedResponse
from app.services.activity.activity import get_activity_by_id_service
from app.services.utils.query import paginated_query


def get_assets_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: AssetFilter,
) -> PaginatedResponse[AssetRead]:
    """
    Get all assets for an assessment. Searchable by name.
    """
    base_statement = select(Asset).where(Asset.assessment_id == assessment_id)

    if user.assessment_acl_role == AclRole.SPECTATOR:
        base_statement = base_statement.filter(Asset.deleted.is_(False))

    return paginated_query(session, Asset, filter_query, base_statement=base_statement)


def get_asset_by_id_service(
    asset_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> AssetRead:
    """
    Get a specific asset for an assessment.
    """
    statement = select(Asset).where(
        Asset.id == asset_id, Asset.assessment_id == assessment_id
    )
    asset = session.execute(statement).unique().scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return asset


def create_asset_service(
    asset: AssetBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> AssetRead:
    """
    Create a new asset for an assessment.
    """
    new_asset = Asset(
        name=asset.name,
        icon=asset.icon,
        properties=asset.properties,
        assessment_id=assessment_id,
        created_by=user.id,
    )
    session.add(new_asset)
    session.commit()
    return new_asset


def update_asset_service(
    asset_id: uuid.UUID,
    asset: AssetBase,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> AssetRead:
    """
    Update a specific asset for an assessment.
    """
    asset_db = get_asset_by_id_service(asset_id, assessment_id, user, session)
    asset_db.name = asset.name
    asset_db.icon = asset.icon
    asset_db.properties = asset.properties
    asset_db.updated_by = user.id
    session.commit()
    return asset_db


def toggle_asset_delete_service(
    asset_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Toggle the deleted flag for a specific asset for an assessment.
    """
    asset = get_asset_by_id_service(asset_id, assessment_id, user, session)
    if asset.deleted:
        asset.deleted = False
        asset.deleted_at = None
        asset.deleted_by = None
    else:
        asset.deleted = True
        asset.deleted_at = func.now()
        asset.deleted_by = user.id
    session.commit()


def get_assets_by_ids_service(
    asset_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> list[Asset]:
    """
    Get multiple assets by their IDs and validate they belong to the assessment.
    Raises HTTPException if any asset is not found or belongs to different assessment.
    """
    if not asset_ids:
        return []

    statement = select(Asset).where(
        Asset.id.in_(asset_ids),
        Asset.assessment_id == assessment_id,
    )
    assets = session.execute(statement).scalars().unique().all()

    # Validate all assets exist
    if len(assets) != len(asset_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more assets not found or do not belong to this assessment",
        )

    return assets


def assign_assets_to_activity(
    activity_id: uuid.UUID,
    role: ActivityAssetRole,
    asset_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """
    Assign assets to an activity with a specific role.
    Replaces all existing assets for this role.
    Validates that all assets belong to the same assessment as the activity.
    """
    # Validate activity exists and belongs to assessment
    get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Get and validate assets if provided
    if asset_ids:
        assets = get_assets_by_ids_service(asset_ids, assessment_id, user, session)

        # Remove existing assignments for this activity and role
        delete_stmt = delete(activity_asset_association).where(
            activity_asset_association.c.activity_id == activity_id,
            activity_asset_association.c.role == role.value,
        )
        session.execute(delete_stmt)

        # Add new assignments
        for asset in assets:
            insert_stmt = activity_asset_association.insert().values(
                activity_id=activity_id,
                asset_id=asset.id,
                role=role.value,
            )
            session.execute(insert_stmt)
    else:
        # Empty list means remove all assets for this role
        delete_stmt = delete(activity_asset_association).where(
            activity_asset_association.c.activity_id == activity_id,
            activity_asset_association.c.role == role.value,
        )
        session.execute(delete_stmt)

    session.commit()
