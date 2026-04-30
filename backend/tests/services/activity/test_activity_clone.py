from app.enums.enums import AclRole
from app.models.activity import Activity, activity_asset_association
from app.models.assessment import Assessment  # Assuming this exists
from app.models.asset import Asset
from app.models.tag import Tag
from app.models.user import User
from app.services.activity.activity import clone_activity_service


def test_clone_activity_service(session):
    # 1. Setup Data
    user = User(email="test_clone@example.com")
    user.assessment_acl_role = AclRole.RED
    session.add(user)

    assessment = Assessment(
        name="Test Assessment", description="Desc", assessment_type="PurpleTeam"
    )
    session.add(assessment)
    session.flush()

    tag = Tag(name="Test Tag", color="#000000", assessment_id=assessment.id)
    session.add(tag)

    asset = Asset(name="Test Asset", assessment_id=assessment.id)
    session.add(asset)

    session.commit()

    # 2. Create Original Activity
    activity = Activity(
        name="Original Activity",
        mitre_tactic="Tactic",
        mitre_technique="Technique",
        assessment_id=assessment.id,
        tags=[tag],
    )
    session.add(activity)
    session.flush()  # get ID

    # Add Asset Association manually or via relationship?
    # ViewOnly means we can't append to relationship directly usually, but let's see.
    # The models file showed viewonly=True. So we must insert into association table.
    session.execute(
        activity_asset_association.insert().values(
            activity_id=activity.id, asset_id=asset.id, role="source"
        )
    )
    session.commit()

    # Verify setup
    session.refresh(activity)
    assert len(activity.tags) == 1
    # Check sources
    sources = (
        session.query(Asset)
        .join(
            activity_asset_association,
            Asset.id == activity_asset_association.c.asset_id,
        )
        .filter(
            activity_asset_association.c.activity_id == activity.id,
            activity_asset_association.c.role == "source",
        )
        .all()
    )
    assert len(sources) == 1

    # 3. Clone
    cloned_activity = clone_activity_service(activity.id, assessment.id, user, session)

    # 4. Verify Clone
    assert cloned_activity.id != activity.id
    assert cloned_activity.name == "Original Activity (Copy)"
    assert cloned_activity.mitre_tactic == "Tactic"

    # Verify Tags
    assert len(cloned_activity.tags) == 1
    assert cloned_activity.tags[0].id == tag.id

    # Verify Assets (Sources)
    cloned_sources = (
        session.query(Asset)
        .join(
            activity_asset_association,
            Asset.id == activity_asset_association.c.asset_id,
        )
        .filter(
            activity_asset_association.c.activity_id == cloned_activity.id,
            activity_asset_association.c.role == "source",
        )
        .all()
    )

    assert len(cloned_sources) == 0
