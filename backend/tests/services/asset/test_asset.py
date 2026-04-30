import uuid

import pytest
from fastapi import HTTPException

from app.enums.enums import ActivityAssetRole
from app.models.activity import Activity
from app.models.assessment import Assessment
from app.schemas.asset import AssetBase, AssetFilter
from app.services.asset.asset import (
    assign_assets_to_activity,
    create_asset_service,
    get_asset_by_id_service,
    get_assets_by_ids_service,
    get_assets_service,
    toggle_asset_delete_service,
    update_asset_service,
)


@pytest.fixture
def test_assessment(session, test_admin_user):
    assessment = Assessment(
        name="Test Assessment",
        description="Description",
        assessment_type="PurpleTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def test_create_asset(session, test_assessment, test_admin_user):
    asset_data = AssetBase(
        name="Test Asset", icon="server", properties={"ip": "10.0.0.1"}
    )
    asset = create_asset_service(
        asset_data, test_assessment.id, test_admin_user, session
    )

    assert asset.name == "Test Asset"
    assert asset.icon == "server"
    assert asset.properties == {"ip": "10.0.0.1"}
    assert asset.assessment_id == test_assessment.id
    assert asset.deleted is False


def test_get_assets(session, test_assessment, test_admin_user):
    asset1 = AssetBase(name="Asset 1", icon="server", properties={})
    asset2 = AssetBase(name="Asset 2", icon="laptop", properties={})

    create_asset_service(asset1, test_assessment.id, test_admin_user, session)
    create_asset_service(asset2, test_assessment.id, test_admin_user, session)

    assets = get_assets_service(
        test_assessment.id, test_admin_user, session, AssetFilter()
    )
    assert assets.total == 2


def test_get_assets_with_filter(session, test_assessment, test_admin_user):
    asset1 = AssetBase(name="WebServer", icon="server", properties={})
    asset2 = AssetBase(name="Database", icon="database", properties={})

    create_asset_service(asset1, test_assessment.id, test_admin_user, session)
    create_asset_service(asset2, test_assessment.id, test_admin_user, session)

    assets = get_assets_service(
        test_assessment.id, test_admin_user, session, AssetFilter(name="Web")
    )
    assert assets.total == 1
    assert assets.items[0].name == "WebServer"


def test_get_asset_by_id(session, test_assessment, test_admin_user):
    asset_data = AssetBase(name="Test Asset", icon="server", properties={})
    created_asset = create_asset_service(
        asset_data, test_assessment.id, test_admin_user, session
    )

    fetched_asset = get_asset_by_id_service(
        created_asset.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_asset.id == created_asset.id
    assert fetched_asset.name == "Test Asset"


def test_get_asset_by_id_not_found(session, test_assessment, test_admin_user):
    with pytest.raises(HTTPException) as exc:
        get_asset_by_id_service(
            uuid.uuid4(), test_assessment.id, test_admin_user, session
        )
    assert exc.value.status_code == 404


def test_update_asset(session, test_assessment, test_admin_user):
    asset_data = AssetBase(name="Original Name", icon="server", properties={})
    created_asset = create_asset_service(
        asset_data, test_assessment.id, test_admin_user, session
    )

    update_data = AssetBase(
        name="Updated Name", icon="laptop", properties={"changed": True}
    )
    updated_asset = update_asset_service(
        created_asset.id, update_data, test_assessment.id, test_admin_user, session
    )

    assert updated_asset.name == "Updated Name"
    assert updated_asset.icon == "laptop"
    assert updated_asset.properties == {"changed": True}


def test_toggle_asset_delete(session, test_assessment, test_admin_user):
    asset_data = AssetBase(name="Test Asset", icon="server", properties={})
    created_asset = create_asset_service(
        asset_data, test_assessment.id, test_admin_user, session
    )

    # Delete
    toggle_asset_delete_service(
        created_asset.id, test_assessment.id, test_admin_user, session
    )
    fetched_asset = get_asset_by_id_service(
        created_asset.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_asset.deleted is True

    # Undelete
    toggle_asset_delete_service(
        created_asset.id, test_assessment.id, test_admin_user, session
    )
    fetched_asset = get_asset_by_id_service(
        created_asset.id, test_assessment.id, test_admin_user, session
    )
    assert fetched_asset.deleted is False


def test_get_assets_by_ids(session, test_assessment, test_admin_user):
    a1 = create_asset_service(
        AssetBase(name="A1", icon="s", properties={}),
        test_assessment.id,
        test_admin_user,
        session,
    )
    a2 = create_asset_service(
        AssetBase(name="A2", icon="s", properties={}),
        test_assessment.id,
        test_admin_user,
        session,
    )

    results = get_assets_by_ids_service(
        [a1.id, a2.id], test_assessment.id, test_admin_user, session
    )
    assert len(results) == 2


def test_get_assets_by_ids_not_found(session, test_assessment, test_admin_user):
    a1 = create_asset_service(
        AssetBase(name="A1", icon="s", properties={}),
        test_assessment.id,
        test_admin_user,
        session,
    )

    with pytest.raises(HTTPException) as exc:
        get_assets_by_ids_service(
            [a1.id, uuid.uuid4()], test_assessment.id, test_admin_user, session
        )
    assert exc.value.status_code == 404


def test_assign_assets_to_activity(session, test_assessment, test_admin_user):
    # Create assets
    a1 = create_asset_service(
        AssetBase(name="Source", icon="s", properties={}),
        test_assessment.id,
        test_admin_user,
        session,
    )
    a2 = create_asset_service(
        AssetBase(name="Target", icon="t", properties={}),
        test_assessment.id,
        test_admin_user,
        session,
    )

    # Create activity
    activity = Activity(
        assessment_id=test_assessment.id,
        name="Test Activity",
        mitre_tactic="Tactic",
        mitre_technique="T1234",
        created_by=test_admin_user.id,
    )
    session.add(activity)
    session.commit()

    # Assign sources
    assign_assets_to_activity(
        activity.id,
        ActivityAssetRole.SOURCE,
        [a1.id],
        test_assessment.id,
        test_admin_user,
        session,
    )

    # Assign targets
    assign_assets_to_activity(
        activity.id,
        ActivityAssetRole.TARGET,
        [a2.id],
        test_assessment.id,
        test_admin_user,
        session,
    )

    # Refresh and check
    session.refresh(activity)
    assert len(activity.sources) == 1
    assert activity.sources[0].id == a1.id
    assert len(activity.targets) == 1
    assert activity.targets[0].id == a2.id
