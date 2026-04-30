import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
import yaml
from sqlalchemy import select

from app.models.activity_group_template import ActivityGroupTemplate
from app.models.activity_template import ActivityTemplate
from app.models.user import User
from app.services.seed.custom_data import (
    import_custom_data_service,
)


@pytest.fixture
def mock_zip_content_with_groups():
    """Create a zip with activities, group templates, and no activityGroups in activities."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Activity templates (no activityGroups field)
        activity_a = {
            "name": "Activity Alpha",
            "mitreTactic": "Test Tactic",
            "mitreTechnique": "T1234",
            "activityRationale": "Rationale A",
            "provider": "TestProvider",
        }
        z.writestr("templates/activities/activity_alpha.yaml", yaml.dump(activity_a))

        activity_b = {
            "name": "Activity Beta",
            "mitreTactic": "Test Tactic",
            "mitreTechnique": "T1235",
            "activityRationale": "Rationale B",
            "provider": "TestProvider",
        }
        z.writestr("templates/activities/activity_beta.yaml", yaml.dump(activity_b))

        activity_c = {
            "name": "Activity Charlie",
            "mitreTactic": "Test Tactic",
            "mitreTechnique": "T1236",
            "activityRationale": "Rationale C",
            "provider": "TestProvider",
        }
        z.writestr("templates/activities/activity_charlie.yaml", yaml.dump(activity_c))

        # Group templates referencing activities by name
        group_data = {
            "name": "Group A",
            "activities": ["Activity Alpha", "Activity Beta"],
        }
        z.writestr("templates/groups/group_a.yaml", yaml.dump(group_data))

        group_data_2 = {
            "name": "Group B",
            "activities": ["Activity Beta", "Activity Charlie"],
        }
        z.writestr("templates/groups/group_b.yaml", yaml.dump(group_data_2))

    buffer.seek(0)
    return buffer.getvalue()


def test_import_custom_data_with_group_templates(session, mock_zip_content_with_groups):
    """Test that group templates import correctly via import_custom_data_service."""
    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = "https://example.com/repo.zip"
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        with patch("app.services.seed.custom_data.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_zip_content_with_groups
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            user = User(email="test_group_import@example.com")
            session.add(user)
            session.commit()

            result_msg = import_custom_data_service(user, session)

            # Verify message
            assert "Activities: 3 success" in result_msg
            assert "Groups: 2 success" in result_msg

            # Verify Activity Templates
            activities = session.execute(select(ActivityTemplate)).scalars().all()
            assert len(activities) == 3

            # Verify Groups created from group template files
            groups = session.execute(select(ActivityGroupTemplate)).scalars().all()
            assert len(groups) == 2
            group_names = sorted([g.name for g in groups])
            assert group_names == ["Group A", "Group B"]

            # Verify Group A associations
            group_a = next(g for g in groups if g.name == "Group A")
            group_a_activity_names = [a.name for a in group_a.activity_templates]
            assert group_a_activity_names == [
                "Activity Alpha",
                "Activity Beta",
            ]

            # Verify Group B associations
            group_b = next(g for g in groups if g.name == "Group B")
            group_b_activity_names = [a.name for a in group_b.activity_templates]
            assert group_b_activity_names == [
                "Activity Beta",
                "Activity Charlie",
            ]


def test_import_activities_no_longer_create_groups(session):
    """Test that activities with activityGroups field do NOT create group templates."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Activity with activityGroups (should be ignored now)
        activity_data = {
            "name": "Old Style Activity",
            "mitreTactic": "Test Tactic",
            "mitreTechnique": "T1234",
            "activityRationale": "Rationale",
            "provider": "TestProvider",
            "activityGroups": ["Legacy Group"],
        }
        z.writestr("templates/activities/old_style.yaml", yaml.dump(activity_data))

    buffer.seek(0)
    zip_content = buffer.getvalue()

    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = "https://example.com/repo.zip"
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        with patch("app.services.seed.custom_data.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = zip_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            user = User(email="test_no_groups@example.com")
            session.add(user)
            session.commit()

            result_msg = import_custom_data_service(user, session)

            assert "Activities: 1 success" in result_msg

            # Activity should exist
            activities = session.execute(select(ActivityTemplate)).scalars().all()
            assert len(activities) == 1

            # No groups should have been created from activityGroups field
            groups = session.execute(select(ActivityGroupTemplate)).scalars().all()
            assert len(groups) == 0
