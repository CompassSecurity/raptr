import io
import zipfile

import httpx
import yaml
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.enums.enums import ReportTemplateFormat
from app.models.activity_group_template import (
    ActivityGroupTemplate,
    activity_template_activity_group,
)
from app.models.activity_template import ActivityTemplate
from app.models.campaign_template import CampaignTemplate, CampaignTemplateItem
from app.models.evaluation_template import EvaluationTemplate
from app.models.knowledge_base import KnowledgeBase
from app.models.report_template import ReportTemplate
from app.models.user import User
from app.schemas.activity_template import ActivityTemplateBase
from app.services.utils.memory import release_memory


def import_custom_activity_templates_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import custom activity templates from git repository (downloaded as zip).
    Groups and campaigns are imported separately.
    """
    try:
        # Remove existing activity group associations
        session.execute(delete(activity_template_activity_group))
        # Remove existing campaign template items and campaigns
        session.execute(delete(CampaignTemplateItem))
        session.execute(delete(CampaignTemplate))
        # Remove existing activities, preserving those with the 'ART' provider
        session.execute(
            delete(ActivityTemplate).where(ActivityTemplate.provider != "ART")
        )
        # Remove existing activity groups
        session.execute(delete(ActivityGroupTemplate))
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to clear existing activities: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear existing activities",
        )

    try:
        count = 0
        failed_count = 0

        for filename in zip_file.namelist():
            # Check for yaml extension
            if not filename.endswith(".yaml"):
                continue

            # Check if file is inside a 'templates/activities' directory
            if "templates/activities" not in filename:
                continue

            with zip_file.open(filename) as f:
                try:
                    content = yaml.safe_load(f)
                    if not content:
                        failed_count += 1
                        continue

                    try:
                        # Map YAML keys to Pydantic/Model keys
                        activity_data = {
                            "name": content.get("name"),
                            "mitre_tactic": content.get("mitreTactic"),
                            "mitre_technique": content.get("mitreTechnique"),
                            "activity_rationale": content.get("activityRationale", ""),
                            "activity_actions": content.get("activityActions", ""),
                            "activity_requirements": content.get(
                                "activityRequirements", ""
                            ),
                            "activity_notes": content.get("activityNotes", ""),
                            "provider": content.get("provider", "Custom"),
                            "expected_logging": content.get("expectedLogging", False),
                            "expected_prevention": content.get(
                                "expectedPrevention", False
                            ),
                            "expected_alert_creation": content.get(
                                "expectedAlertCreation", False
                            ),
                            "expected_stakeholder_notification": content.get(
                                "expectedStakeholderNotification", False
                            ),
                            "expected_severity": content.get("expectedseverity", "Low"),
                            "priority": content.get("priority", "Low"),
                            "linked_knowledge_base_articles": content.get(
                                "kbArticles", []
                            ),
                        }

                        # Validate with Pydantic
                        validated_activity = ActivityTemplateBase(**activity_data)

                        # Create DB model
                        activity = ActivityTemplate(
                            **validated_activity.model_dump(),
                            created_by=user.id,
                        )

                        session.add(activity)
                        count += 1

                    except ValidationError as e:
                        app_logger.error(f"Validation failed for {filename}: {e}")
                        failed_count += 1
                        continue

                except yaml.YAMLError as e:
                    app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                    failed_count += 1
                    continue

        session.commit()
        return count, failed_count

    except Exception as e:
        app_logger.error(f"An unexpected error occurred during activity import: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import custom activities",
        )


def import_custom_group_templates_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import group templates from a zip file.
    Expects templates to be in a 'groups/' directory within the zip.
    Groups reference activities by name and define ordering.
    Must be called AFTER import_custom_activity_templates_service.
    """
    count = 0
    failed_count = 0

    for filename in zip_file.namelist():
        if not filename.endswith(".yaml"):
            continue

        if "templates/groups" not in filename:
            continue

        with zip_file.open(filename) as f:
            try:
                content = yaml.safe_load(f)
                if not content:
                    failed_count += 1
                    continue

                name = content.get("name")
                if not name:
                    app_logger.warning(f"Skipping {filename}: Missing 'name'")
                    failed_count += 1
                    continue

                description = content.get("description")
                activity_names = content.get("activities", [])

                # Create the group template
                group = ActivityGroupTemplate(
                    name=name,
                    description=description,
                    created_by=user.id,
                )
                session.add(group)
                session.flush()  # Get the group ID

                # Link activities by name with position
                for position, activity_name in enumerate(activity_names):
                    stmt = select(ActivityTemplate).where(
                        ActivityTemplate.name == activity_name
                    )
                    activity = session.execute(stmt).scalar_one_or_none()
                    if activity:
                        session.execute(
                            activity_template_activity_group.insert().values(
                                activity_template_id=activity.id,
                                activity_group_template_id=group.id,
                                position=position,
                            )
                        )
                    else:
                        app_logger.warning(
                            f"Activity '{activity_name}' not found for group '{name}'"
                        )

                count += 1

            except yaml.YAMLError as e:
                app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                failed_count += 1
                continue
            except Exception as e:
                app_logger.error(f"Failed to import group template {filename}: {e}")
                failed_count += 1
                continue

    try:
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to commit group templates: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit group templates",
        )

    return count, failed_count


def import_custom_campaign_templates_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import campaign templates from a zip file.
    Expects templates to be in a 'campaigns/' directory within the zip.
    Must be called AFTER both activity and group templates are imported.
    """
    count = 0
    failed_count = 0

    for filename in zip_file.namelist():
        if not filename.endswith(".yaml"):
            continue

        if "templates/campaigns" not in filename:
            continue

        with zip_file.open(filename) as f:
            try:
                content = yaml.safe_load(f)
                if not content:
                    failed_count += 1
                    continue

                name = content.get("name")
                if not name:
                    app_logger.warning(f"Skipping {filename}: Missing 'name'")
                    failed_count += 1
                    continue

                description = content.get("description")

                # Create the campaign template
                campaign = CampaignTemplate(
                    name=name,
                    description=description,
                    created_by=user.id,
                )
                session.add(campaign)
                session.flush()  # Get the campaign ID

                # Create ordered items
                items = content.get("items", [])
                for position, item in enumerate(items):
                    item_type = item.get("type")
                    ref = item.get("ref")

                    if not item_type or not ref:
                        app_logger.warning(
                            f"Skipping invalid item in campaign '{name}': {item}"
                        )
                        continue

                    campaign_item = CampaignTemplateItem(
                        campaign_template_id=campaign.id,
                        position=position,
                        item_type=item_type,
                        created_by=user.id,
                    )

                    if item_type == "group":
                        stmt = select(ActivityGroupTemplate).where(
                            ActivityGroupTemplate.name == ref
                        )
                        group = session.execute(stmt).scalar_one_or_none()
                        if group:
                            campaign_item.activity_group_template_id = group.id
                        else:
                            app_logger.warning(
                                f"Group '{ref}' not found for campaign '{name}'"
                            )
                            continue

                    elif item_type == "activity":
                        stmt = select(ActivityTemplate).where(
                            ActivityTemplate.name == ref
                        )
                        activity = session.execute(stmt).scalar_one_or_none()
                        if activity:
                            campaign_item.activity_template_id = activity.id
                        else:
                            app_logger.warning(
                                f"Activity '{ref}' not found for campaign '{name}'"
                            )
                            continue
                    else:
                        app_logger.warning(
                            f"Unknown item type '{item_type}' in campaign '{name}'"
                        )
                        continue

                    session.add(campaign_item)

                count += 1

            except yaml.YAMLError as e:
                app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                failed_count += 1
                continue
            except Exception as e:
                app_logger.error(f"Failed to import campaign template {filename}: {e}")
                failed_count += 1
                continue

    try:
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to commit campaign templates: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit campaign templates",
        )

    return count, failed_count


def import_knowledge_base_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import knowledge base articles from a zip file.
    Expects KB articles to be in a 'kb/' directory within the zip.
    """
    count = 0
    failed_count = 0

    # 1. Clear existing Knowledge Base entries (optional, but consistent with current import logic)
    # Ideally, we might want to update existing, but simple replacement avoids stale data.
    try:
        session.execute(delete(KnowledgeBase))
        session.flush()  # Flush to ensure deletion happens before insertion
    except Exception as e:
        app_logger.error(f"Failed to clear existing knowledge base: {e}")
        # Continue anyway, upsert will handle updates

    # 2. Iterate through files
    for filename in zip_file.namelist():
        # Check for yaml extension and 'kb' directory
        if not filename.endswith(".yaml"):
            continue

        # Check if file is inside a 'templates/kb' directory
        # e.g templates/kb/article.yaml
        if "templates/kb" not in filename:
            continue

        with zip_file.open(filename) as f:
            try:
                content = yaml.safe_load(f)
                if not content:
                    failed_count += 1
                    continue

                # Basic validation
                name = content.get("name")
                if not name:
                    app_logger.warning(f"Skipping {filename}: Missing 'name'")
                    failed_count += 1
                    continue

                mitre_technique_id = content.get("mitre_technique_id")
                # Structure content as JSON
                # We store the whole YAML content as the 'content' field,
                # or we could extract specific sections.
                # Given the flexible requirement, storing the whole dict (minus metadata if desired) is safest.
                # Let's extract metadata and store the rest as content.

                kb_data = {
                    "name": name,
                    "mitre_technique_id": mitre_technique_id,
                    "content": content,  # Store full content for flexibility
                    "created_by": user.id,
                }

                # Upsert logic (PostgreSQL dependent, but we use session.merge/add for abstract support)
                # Since we cleared the table, valid add is fine.
                # However, if duplicate names exist in the zip, last one wins.

                # Check if exists by name (in case of duplicates in zip)
                stmt = select(KnowledgeBase).where(KnowledgeBase.name == name)
                existing = session.execute(stmt).scalars().first()

                if existing:
                    existing.mitre_technique_id = mitre_technique_id
                    existing.content = content
                    existing.created_by = user.id
                else:
                    kb = KnowledgeBase(**kb_data)
                    session.add(kb)

                count += 1

            except yaml.YAMLError as e:
                app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                failed_count += 1
                continue
            except Exception as e:
                app_logger.error(f"Failed to import KB {filename}: {e}")
                failed_count += 1
                continue

    return count, failed_count


def import_evaluation_templates_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import evaluation templates from a zip file.
    Expects templates to be in an 'evaluation/' directory within the zip.
    """
    count = 0
    failed_count = 0

    # 1. Clear existing Evaluation Templates
    # We do NOT clear existing templates to preserve IDs for default configurations.
    # Instead we update existing ones or create new ones.

    # 2. Iterate through files
    for filename in zip_file.namelist():
        if not filename.endswith(".yaml"):
            continue

        # Check if file is inside a 'templates/evaluation' directory
        if "templates/evaluation" not in filename:
            continue

        with zip_file.open(filename) as f:
            try:
                content = yaml.safe_load(f)
                if not content:
                    failed_count += 1
                    continue

                # Mapping
                name = content.get("name")
                evaluation_criteria = content.get("evaluationCriteria")
                description = content.get("description")

                if not name or not evaluation_criteria:
                    app_logger.warning(
                        f"Skipping {filename}: Missing 'name' or 'evaluationCriteria'"
                    )
                    failed_count += 1
                    continue

                # Check if template exists
                statement = select(EvaluationTemplate).where(
                    EvaluationTemplate.name == str(name)
                )
                existing = session.execute(statement).scalar_one_or_none()

                if existing:
                    existing.evaluation_criteria = evaluation_criteria
                    existing.description = description
                else:
                    template = EvaluationTemplate(
                        name=str(name),
                        evaluation_criteria=evaluation_criteria,
                        description=description,
                    )
                    session.add(template)

                count += 1

            except yaml.YAMLError as e:
                app_logger.error(f"Failed to parse YAML file {filename}: {e}")
                failed_count += 1
                continue
            except Exception as e:
                app_logger.error(
                    f"Failed to import Evaluation Template {filename}: {e}"
                )
                failed_count += 1
                continue

    # Commit changes
    try:
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to commit evaluation templates: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit evaluation templates",
        )

    return count, failed_count


def import_report_templates_service(
    user: User,
    session: Session,
    zip_file: zipfile.ZipFile,
) -> tuple[int, int]:
    """
    Import report templates from a zip file.
    Wipes all existing report templates and creates fresh ones.
    Expects templates to be in a 'report/' directory within the zip.
    Supports .html and .docx files.
    """
    # Wipe all existing report templates
    session.execute(delete(ReportTemplate))
    session.flush()

    count = 0
    failed_count = 0

    EXTENSION_FORMAT = {
        ".html": ReportTemplateFormat.HTML,
        ".docx": ReportTemplateFormat.DOCX,
    }

    for filename in zip_file.namelist():
        parts = filename.split("/")
        if "templates/report" not in filename:
            continue

        basename = parts[-1]
        if not basename:
            continue

        ext = None
        for supported_ext in EXTENSION_FORMAT:
            if basename.lower().endswith(supported_ext):
                ext = supported_ext
                break

        if ext is None:
            continue

        try:
            with zip_file.open(filename) as f:
                content = f.read()

            if not content:
                app_logger.warning(f"Skipping empty report template: {basename}")
                failed_count += 1
                continue

            template = ReportTemplate(
                filename=basename,
                format=EXTENSION_FORMAT[ext],
                template_content=content,
            )
            session.add(template)
            count += 1

        except Exception as e:
            app_logger.error(f"Failed to import report template {basename}: {e}")
            failed_count += 1
            continue

    try:
        session.commit()
    except Exception as e:
        app_logger.error(f"Failed to commit report templates: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit report templates",
        )

    return count, failed_count


def import_custom_data_service(
    user: User,
    session: Session,
) -> str:
    """
    Downloads custom data zip and imports both Knowledge Base articles and Activity Templates.
    """
    if not settings.CUSTOM_DATA_URL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom data URL is not configured.",
        )

    url = settings.CUSTOM_DATA_URL
    headers = {}
    if settings.CUSTOM_DATA_TOKEN:
        # Github uses Authorization Bearer, Gitlab uses PRIVATE-TOKEN. For now we just send both headers to support both.
        # If we later decide to support other providers, we might want to add a provider field to the settings and check for it here.
        headers.update(
            {
                "Authorization": f"Bearer {settings.CUSTOM_DATA_TOKEN}",
                "PRIVATE-TOKEN": settings.CUSTOM_DATA_TOKEN,
            }
        )

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        app_logger.error(f"Failed to download custom data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download custom data",
        )

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # 1. Import Knowledge Base
            kb_count, kb_failed_count = import_knowledge_base_service(user, session, z)
            msg_kb = f"Knowledge Base: {kb_count} success, {kb_failed_count} failed"
            app_logger.info(msg_kb)

            # 2. Import Activity Templates
            act_count, act_failed_count = import_custom_activity_templates_service(
                user, session, z
            )
            msg_act = f"Activities: {act_count} success, {act_failed_count} failed"
            app_logger.info(msg_act)

            # 3. Import Group Templates (must be after activities)
            grp_count, grp_failed_count = import_custom_group_templates_service(
                user, session, z
            )
            msg_grp = f"Groups: {grp_count} success, {grp_failed_count} failed"
            app_logger.info(msg_grp)

            # 4. Import Campaign Templates (must be after activities and groups)
            cmp_count, cmp_failed_count = import_custom_campaign_templates_service(
                user, session, z
            )
            msg_cmp = f"Campaigns: {cmp_count} success, {cmp_failed_count} failed"
            app_logger.info(msg_cmp)

            # 5. Import Evaluation Templates
            eval_count, eval_failed_count = import_evaluation_templates_service(
                user, session, z
            )
            msg_eval = f"Evaluations: {eval_count} success, {eval_failed_count} failed"
            app_logger.info(msg_eval)

            # 6. Import Report Templates
            rpt_count, rpt_failed_count = import_report_templates_service(
                user, session, z
            )
            msg_rpt = (
                f"Report Templates: {rpt_count} success, {rpt_failed_count} failed"
            )
            app_logger.info(msg_rpt)

            msg = f"Import completed. {msg_kb}. {msg_act}. {msg_grp}. {msg_cmp}. {msg_eval}. {msg_rpt}."

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zip file format"
        )
    except Exception as e:
        app_logger.error(f"Import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import process failed: {str(e)}",
        )

    del response
    release_memory()
    return msg
