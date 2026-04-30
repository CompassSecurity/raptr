import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import HTTPException

from app.models.activity_template import ActivityTemplate
from app.models.mitre import Tactic, Technique
from app.models.user import User
from app.services.seed.art import import_atomic_red_team_activity_templates_service
from app.services.seed.custom_data import (
    import_custom_data_service,
)


@pytest.fixture
def mock_zip_content():
    # Create a dummy zip file in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Valid activity
        activity_data = {
            "name": "Test Activity",
            "mitreTactic": "Test Tactic",
            "mitreTechnique": "T1234",
            "activityRationale": "Rationale",
            "activityActions": "Actions",
            "activityRequirements": "Requirements",
            "activityNotes": "Notes",
            "provider": "TestProvider",
            "expectedPrevention": True,
            "expectedAlertCreation": True,
            "expectedseverity": "High",
            "priority": "High",
        }
        z.writestr("templates/activities/test_activity.yaml", yaml.dump(activity_data))

        # Another activity in a subdirectory
        activity_data_2 = activity_data.copy()
        activity_data_2["name"] = "Test Activity 2"
        z.writestr(
            "repo-main/templates/activities/subdir/test_activity_2.yaml",
            yaml.dump(activity_data_2),
        )

        # Non-activity file
        z.writestr("templates/activities/readme.txt", "This is not a yaml file")

    buffer.seek(0)
    return buffer.getvalue()


def test_import_custom_activities_success(session, mock_zip_content):
    # Mock settings
    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = "https://example.com/repo.zip"
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        # Mock httpx
        with patch("app.services.seed.custom_data.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_zip_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Create dummy user
            user = User(email="test@example.com")
            session.add(user)
            session.commit()

            # Call service
            result_msg = import_custom_data_service(user, session)

            # Verify message
            assert "Activities: 2 success" in result_msg
            assert "0 failed" in result_msg

            # Verify DB
            activities = session.query(ActivityTemplate).all()
            assert len(activities) == 2

            names = [a.name for a in activities]
            assert "Test Activity" in names
            assert "Test Activity 2" in names
            assert activities[0].created_by == user.id


def test_import_custom_activities_no_url(session):
    with patch("app.services.seed.custom_data.settings") as mock_settings:
        mock_settings.CUSTOM_DATA_URL = None
        mock_settings.CUSTOM_DATA_TOKEN = "test-token"

        user = User(email="test2@example.com")
        session.add(user)
        session.commit()

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc:
            import_custom_data_service(user, session)
        assert exc.value.status_code == 400
        assert "Custom data URL is not configured." in exc.value.detail


# Atomic Red Team Import Tests


@pytest.fixture
def mock_art_zip_content():
    """Create a mock Atomic Red Team zip file structure"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Valid ART test case with full structure
        art_data = {
            "attack_technique": "T1059.001",
            "display_name": "PowerShell",
            "atomic_tests": [
                {
                    "name": "PowerShell Test 1",
                    "description": "Execute PowerShell command",
                    "executor": {"name": "powershell", "command": "Write-Host 'Hello'"},
                },
                {
                    "name": "PowerShell Test 2 with variables",
                    "description": "Execute with variables",
                    "executor": {
                        "name": "powershell",
                        "command": "Get-Process -Name #{process_name}",
                    },
                    "input_arguments": {
                        "process_name": {"description": "Process", "default": "notepad"}
                    },
                },
            ],
        }
        z.writestr(
            "atomic-red-team-master/atomics/T1059.001/T1059.001.yaml",
            yaml.dump(art_data),
        )

        # Another technique
        art_data_2 = {
            "attack_technique": "T1003",
            "display_name": "OS Credential Dumping",
            "atomic_tests": [
                {
                    "name": "Credential Dump Test",
                    "description": "Dump credentials",
                    "executor": {
                        "name": "command_prompt",
                        "command": "reg save HKLM\\SAM sam.hiv",
                    },
                }
            ],
        }
        z.writestr(
            "atomic-red-team-master/atomics/T1003/T1003.yaml", yaml.dump(art_data_2)
        )

        # YAML without atomic_tests (should be skipped)
        invalid_data = {"attack_technique": "T9999", "display_name": "Invalid"}
        z.writestr(
            "atomic-red-team-master/atomics/T9999/T9999.yaml", yaml.dump(invalid_data)
        )

        # YAML with test without executor command (should be skipped)
        no_executor_data = {
            "attack_technique": "T8888",
            "atomic_tests": [
                {
                    "name": "Test without executor",
                    "description": "This has no command",
                    "executor": {"name": "manual"},
                }
            ],
        }
        z.writestr(
            "atomic-red-team-master/atomics/T8888/T8888.yaml",
            yaml.dump(no_executor_data),
        )

        # Non-YAML file (should be ignored)
        z.writestr("atomic-red-team-master/atomics/README.md", "# README")

    buffer.seek(0)
    return buffer.getvalue()


def test_import_atomic_red_team_success(session, mock_art_zip_content):
    """Test successful import of Atomic Red Team templates with tactic lookup"""
    # Create MITRE data in database for tactic lookup
    tactic = Tactic(
        mitre_id="TA0002",
        name="Execution",
        url="https://attack.mitre.org/tactics/TA0002",
    )
    session.add(tactic)
    session.commit()

    technique1 = Technique(
        mitre_id="T1059.001",
        name="PowerShell",
        url="https://attack.mitre.org/techniques/T1059/001",
    )
    technique1.tactics.append(tactic)
    session.add(technique1)

    technique2 = Technique(
        mitre_id="T1003",
        name="OS Credential Dumping",
        url="https://attack.mitre.org/techniques/T1003",
    )
    technique2.tactics.append(tactic)
    session.add(technique2)
    session.commit()

    # Mock settings
    with patch("app.services.seed.art.settings") as mock_settings:
        mock_settings.ATOMIC_RED_TEAM_URL = "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"

        # Mock httpx
        with patch("app.services.seed.art.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_art_zip_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Create test user
            user = User(email="art_test@example.com")
            session.add(user)
            session.commit()

            # Call service
            result_msg = import_atomic_red_team_activity_templates_service(
                user, session
            )

            # Verify message - 3 successful (2 from T1059.001, 1 from T1003)
            # 2 failed (1 without atomic_tests, 1 without executor command)
            assert "Atomic Red Team templates imported" in result_msg
            assert "Successful: 3" in result_msg
            assert "Failed: 2" in result_msg

            # Verify DB
            activities = (
                session.query(ActivityTemplate)
                .filter(ActivityTemplate.provider == "ART")
                .all()
            )
            assert len(activities) == 3

            # Check specific activity with tactic lookup
            ps_activity = next(
                (a for a in activities if a.name == "PowerShell Test 1"), None
            )
            assert ps_activity is not None
            assert ps_activity.mitre_technique == "T1059.001"
            assert ps_activity.mitre_tactic == "Execution"  # From DB lookup
            assert ps_activity.activity_rationale == "Execute PowerShell command"
            assert ps_activity.activity_actions == "Write-Host 'Hello'"
            assert ps_activity.provider == "ART"
            assert ps_activity.created_by == user.id

            # Check variable substitution
            ps_var_activity = next(
                (a for a in activities if a.name == "PowerShell Test 2 with variables"),
                None,
            )
            assert ps_var_activity is not None
            assert "Get-Process -Name notepad" in ps_var_activity.activity_actions
            assert "#{process_name}" not in ps_var_activity.activity_actions


def test_import_atomic_red_team_no_url(session):
    """Test that import fails when ATOMIC_RED_TEAM_URL is not set"""
    with patch("app.services.seed.art.settings") as mock_settings:
        mock_settings.ATOMIC_RED_TEAM_URL = None

        user = User(email="art_test2@example.com")
        session.add(user)
        session.commit()

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc:
            import_atomic_red_team_activity_templates_service(user, session)
        assert exc.value.status_code == 400
        assert "ATOMIC_RED_TEAM_URL not set" in exc.value.detail


def test_import_atomic_red_team_download_failure(session):
    """Test that import fails gracefully when download fails"""
    with patch("app.services.seed.art.settings") as mock_settings:
        mock_settings.ATOMIC_RED_TEAM_URL = "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"

        # Mock httpx to raise an error
        with patch("app.services.seed.art.httpx.get") as mock_get:
            import httpx

            mock_get.side_effect = httpx.HTTPError("Network error")

            user = User(email="art_test3@example.com")
            session.add(user)
            session.commit()

            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc:
                import_atomic_red_team_activity_templates_service(user, session)
            assert exc.value.status_code == 500
            assert "Failed to download Atomic Red Team archive" in exc.value.detail


def test_import_atomic_red_team_without_tactic_in_db(session, mock_art_zip_content):
    """Test import when technique exists but has no tactics in DB"""
    # Create technique without tactics
    technique = Technique(
        mitre_id="T1059.001",
        name="PowerShell",
        url="https://attack.mitre.org/techniques/T1059/001",
    )
    session.add(technique)
    session.commit()

    with patch("app.services.seed.art.settings") as mock_settings:
        mock_settings.ATOMIC_RED_TEAM_URL = "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"

        with patch("app.services.seed.art.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_art_zip_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            user = User(email="art_test4@example.com")
            session.add(user)
            session.commit()

            # Should still work, but tactic will be empty
            result_msg = import_atomic_red_team_activity_templates_service(
                user, session
            )
            assert "Atomic Red Team templates imported" in result_msg

            # Verify tactic is empty string
            activities = (
                session.query(ActivityTemplate)
                .filter(ActivityTemplate.provider == "ART")
                .all()
            )
            ps_activity = next(
                (a for a in activities if a.name == "PowerShell Test 1"), None
            )
            assert ps_activity is not None
            assert ps_activity.mitre_tactic == ""  # Empty because no tactics in DB


def test_import_atomic_red_team_clears_existing(session, mock_art_zip_content):
    """Test that import clears existing ART templates before importing new ones"""
    # Create existing ART activity
    user = User(email="art_test5@example.com")
    session.add(user)
    session.commit()

    existing_activity = ActivityTemplate(
        name="Old ART Activity",
        mitre_tactic="Old Tactic",
        mitre_technique="T0000",
        activity_rationale="Old",
        activity_actions="Old",
        provider="ART",
        created_by=user.id,
    )
    session.add(existing_activity)
    session.commit()

    # Verify it exists
    assert (
        session.query(ActivityTemplate)
        .filter(ActivityTemplate.provider == "ART")
        .count()
        == 1
    )

    # Import new activities
    with patch("app.services.seed.art.settings") as mock_settings:
        mock_settings.ATOMIC_RED_TEAM_URL = "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"

        with patch("app.services.seed.art.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_art_zip_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            import_atomic_red_team_activity_templates_service(user, session)

            # Old activity should be gone, new ones should exist
            art_activities = (
                session.query(ActivityTemplate)
                .filter(ActivityTemplate.provider == "ART")
                .all()
            )
            assert all(a.name != "Old ART Activity" for a in art_activities)
            assert len(art_activities) >= 3  # New activities imported
