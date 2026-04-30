import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
import yaml
from sqlalchemy import select

from app.models.campaign_template import CampaignTemplate, CampaignTemplateItem
from app.models.user import User
from app.services.seed.custom_data import (
    import_custom_data_service,
)


@pytest.fixture
def mock_zip_content_with_campaign():
    """Create a zip with activities, groups, and a campaign template."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Activities
        for name, technique in [
            ("Activity Alpha", "T1234"),
            ("Activity Beta", "T1235"),
            ("Activity Charlie", "T1236"),
            ("Activity Delta", "T1237"),
        ]:
            data = {
                "name": name,
                "mitreTactic": "Test Tactic",
                "mitreTechnique": technique,
                "activityRationale": f"Rationale for {name}",
                "provider": "TestProvider",
            }
            z.writestr(
                f"templates/activities/{name.lower().replace(' ', '_')}.yaml",
                yaml.dump(data),
            )

        # Groups
        z.writestr(
            "templates/groups/group_a.yaml",
            yaml.dump(
                {"name": "Group A", "activities": ["Activity Alpha", "Activity Beta"]}
            ),
        )
        z.writestr(
            "templates/groups/group_b.yaml",
            yaml.dump({"name": "Group B", "activities": ["Activity Charlie"]}),
        )

        # Campaign
        campaign = {
            "name": "Test Campaign",
            "description": "A test campaign",
            "items": [
                {"type": "group", "ref": "Group A"},
                {"type": "group", "ref": "Group B"},
                {"type": "activity", "ref": "Activity Delta"},
            ],
        }
        z.writestr("templates/campaigns/test_campaign.yaml", yaml.dump(campaign))

    buffer.seek(0)
    return buffer.getvalue()


def test_import_custom_data_with_campaign_template(
    session, mock_zip_content_with_campaign
):
    """Test full import pipeline: activities -> groups -> campaign."""
    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = "https://example.com/repo.zip"
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        with patch("app.services.seed.custom_data.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_zip_content_with_campaign
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            user = User(email="test_campaign_import@example.com")
            session.add(user)
            session.commit()

            result_msg = import_custom_data_service(user, session)

            # Verify message
            assert "Activities: 4 success" in result_msg
            assert "Groups: 2 success" in result_msg
            assert "Campaigns: 1 success" in result_msg

            # Verify Campaign Template
            campaigns = session.execute(select(CampaignTemplate)).scalars().all()
            assert len(campaigns) == 1
            campaign = campaigns[0]
            assert campaign.name == "Test Campaign"
            assert campaign.description == "A test campaign"

            # Verify Campaign Items (ordered)
            items = (
                session.execute(
                    select(CampaignTemplateItem)
                    .where(CampaignTemplateItem.campaign_template_id == campaign.id)
                    .order_by(CampaignTemplateItem.position)
                )
                .scalars()
                .all()
            )
            assert len(items) == 3

            # Item 0: Group A
            assert items[0].item_type == "group"
            assert items[0].position == 0
            assert items[0].activity_group_template_id is not None
            assert items[0].activity_template_id is None

            # Item 1: Group B
            assert items[1].item_type == "group"
            assert items[1].position == 1

            # Item 2: Activity Delta (ungrouped)
            assert items[2].item_type == "activity"
            assert items[2].position == 2
            assert items[2].activity_template_id is not None
            assert items[2].activity_group_template_id is None


def test_campaign_import_missing_refs(session):
    """Test that campaign import gracefully handles missing group/activity refs."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(
            "templates/activities/a.yaml",
            yaml.dump(
                {
                    "name": "Existing Activity",
                    "mitreTactic": "T",
                    "mitreTechnique": "T1",
                    "activityRationale": "R",
                    "provider": "P",
                }
            ),
        )
        z.writestr(
            "templates/campaigns/c.yaml",
            yaml.dump(
                {
                    "name": "Campaign With Missing Refs",
                    "items": [
                        {"type": "group", "ref": "Nonexistent Group"},
                        {"type": "activity", "ref": "Nonexistent Activity"},
                        {"type": "activity", "ref": "Existing Activity"},
                    ],
                }
            ),
        )

    buffer.seek(0)

    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = "https://example.com/repo.zip"
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        with patch("app.services.seed.custom_data.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = buffer.getvalue()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            user = User(email="test_missing_refs@example.com")
            session.add(user)
            session.commit()

            result_msg = import_custom_data_service(user, session)

            # Campaign should still be created
            assert "Campaigns: 1 success" in result_msg

            # Only the valid activity ref should become an item
            campaigns = session.execute(select(CampaignTemplate)).scalars().all()
            assert len(campaigns) == 1
            items = (
                session.execute(
                    select(CampaignTemplateItem).where(
                        CampaignTemplateItem.campaign_template_id == campaigns[0].id
                    )
                )
                .scalars()
                .all()
            )
            # Only "Existing Activity" item should be created (missing refs skipped)
            assert len(items) == 1
            assert items[0].item_type == "activity"
