import io
import zipfile

import httpx
import yaml
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.models.activity_template import ActivityTemplate
from app.models.mitre import Technique
from app.models.user import User
from app.services.utils.memory import release_memory


def import_atomic_red_team_activity_templates_service(
    user: User,
    session: Session,
) -> str:
    """
    Import Atomic Red Team templates from git repository (downloaded as zip, processed in memory).
    """
    atomic_red_team_url = settings.ATOMIC_RED_TEAM_URL

    if not atomic_red_team_url:
        app_logger.warning("ATOMIC_RED_TEAM_URL not set. Skipping import.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ATOMIC_RED_TEAM_URL not set",
        )

    app_logger.debug(f"Importing Atomic Red Team templates from {atomic_red_team_url}")

    # Remove existing Atomic Red Team templates
    try:
        session.execute(
            delete(ActivityTemplate).where(ActivityTemplate.provider == "ART")
        )
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to clear existing ART activities: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear existing ART activities",
        )

    app_logger.debug("Clearing existing ART activities successful")

    # Download the zip archive
    try:
        response = httpx.get(atomic_red_team_url, follow_redirects=True, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        app_logger.error(f"Failed to download Atomic Red Team archive: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download Atomic Red Team archive",
        )

    app_logger.debug("Downloaded Atomic Red Team archive successful")

    # Process the zip file in memory
    try:
        count = 0
        failed_count = 0

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for filename in z.namelist():
                # Only process YAML files in the atomics/T* directories
                # Format: atomic-red-team-master/atomics/T1234/T1234.yaml
                if not filename.endswith(".yaml"):
                    continue

                parts = filename.split("/")
                # Check if file is in atomics directory and starts with T (MITRE technique ID)
                if "atomics" not in parts:
                    continue

                # Find the technique directory (e.g., T1234)
                technique_dir = None
                for part in parts:
                    if part.startswith("T") and part[1:].split(".")[0].isdigit():
                        technique_dir = part
                        break

                if not technique_dir:
                    continue

                # Process the YAML file
                with z.open(filename) as f:
                    try:
                        yml = yaml.safe_load(f)
                        if not yml or "atomic_tests" not in yml:
                            app_logger.warning(
                                f"Skipping {filename}: No atomic_tests found in YAML"
                            )
                            failed_count += 1
                            continue

                        mitre_technique = yml.get("attack_technique", "")

                        # Process each atomic test
                        for art_testcase in yml.get("atomic_tests", []):
                            # Skip if there's no command in the executor
                            if (
                                "executor" not in art_testcase
                                or "command" not in art_testcase["executor"]
                            ):
                                app_logger.debug(
                                    f"Skipping test '{art_testcase.get('name', 'unknown')}' in {filename}: No executor command found"
                                )
                                failed_count += 1
                                continue

                            base_command = art_testcase["executor"]["command"].strip()

                            # Replace input arguments with default values
                            if "input_arguments" in art_testcase and isinstance(
                                art_testcase["input_arguments"], dict
                            ):
                                for arg_name, arg_data in art_testcase[
                                    "input_arguments"
                                ].items():
                                    placeholder = "#{" + arg_name + "}"
                                    default_value = str(arg_data.get("default", ""))
                                    base_command = base_command.replace(
                                        placeholder, default_value
                                    )

                            try:
                                # Lookup tactic from database based on technique
                                mitre_tactic = ""
                                if mitre_technique:
                                    technique = session.scalar(
                                        select(Technique).where(
                                            Technique.mitre_id == mitre_technique
                                        )
                                    )
                                    if technique and technique.tactics:
                                        # Use the first tactic's name
                                        mitre_tactic = technique.tactics[0].name

                                # Create ActivityTemplate
                                activity = ActivityTemplate(
                                    name=art_testcase.get("name", ""),
                                    mitre_tactic=mitre_tactic,
                                    mitre_technique=mitre_technique,
                                    activity_rationale=art_testcase.get(
                                        "description", ""
                                    ),
                                    activity_actions=base_command,
                                    provider="ART",
                                    created_by=user.id,
                                )

                                session.add(activity)
                                count += 1

                            except Exception as e:
                                app_logger.error(
                                    f"Failed to create activity template for {art_testcase.get('name', 'unknown')}: {e}"
                                )
                                failed_count += 1
                                continue

                    except yaml.YAMLError as e:
                        app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                        failed_count += 1
                        continue

        session.commit()
        msg = f"Atomic Red Team templates imported. Successful: {count}, Failed: {failed_count}"
        app_logger.info(msg)

    except zipfile.BadZipFile as e:
        app_logger.error(f"Failed to unzip Atomic Red Team archive: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unzip Atomic Red Team archive",
        )
    except Exception as e:
        app_logger.error(f"An unexpected error occurred during ART import: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import Atomic Red Team templates",
        )

    del response
    release_memory()
    return msg
