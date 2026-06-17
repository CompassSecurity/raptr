import io
import re
import uuid
import zipfile

from fastapi import HTTPException, status
from pathvalidate import sanitize_filename
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.enums.enums import ActivityAssetRole
from app.models.activity import (
    Activity,
    activity_asset_association,
    activity_tag_association,
)
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestions,
)
from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.asset import Asset
from app.models.evaluation_template import EvaluationTemplate
from app.models.file import File
from app.models.tag import Tag
from app.models.user import User
from app.schemas.assessment_export import (
    ActivityExport,
    AssessmentExportData,
    EvaluationExport,
    ImportResponse,
)
from app.services.activity_group.activity_group import get_or_create_default_group
from app.services.utils.memory import release_memory

# Regex to match embedded file URLs in markdown text fields.
# Pattern: /api/v1/assessments/<uuid>/activity/<uuid>/files/<uuid>/download
_FILE_URL_RE = re.compile(
    r"/api/v1/assessments/"
    r"(?P<assessment_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"/activity/"
    r"(?P<activity_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"/files/"
    r"(?P<file_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"/download"
)

# All Activity text fields that may contain embedded file URLs.
_ACTIVITY_TEXT_FIELDS = [
    "activity_rationale",
    "activity_actions",
    "activity_requirements",
    "activity_notes",
    "log_notes",
    "alert_notes",
    "prevent_notes",
    "stakeholder_notification_notes",
]

# ActivityEvaluation evidence fields that may contain embedded file URLs.
_EVALUATION_TEXT_FIELDS = [
    "event_to_alert_data",
    "alert_to_stakeholder_data",
    "alert_severity_data",
    "stakeholder_notification_severity_data",
]

# ActivityEvaluationDynamicQuestions fields.
_DYNAMIC_QUESTION_TEXT_FIELDS = [
    "data",
]


def _build_eval_template_name_map(session: Session) -> dict[str, uuid.UUID]:
    """
    Build a mapping of evaluation template name → ID.
    """
    templates = session.execute(select(EvaluationTemplate)).scalars().all()
    return {t.name: t.id for t in templates}


def _import_evaluation(
    activity_id: uuid.UUID,
    evaluation_data: EvaluationExport,
    template_name_map: dict[str, uuid.UUID],
    warnings: list[str],
    session: Session,
) -> None:
    """
    Create ActivityEvaluation + DynamicQuestions for an imported activity.
    """
    evaluation = ActivityEvaluation(
        activity_id=activity_id,
        logged_evaluation=evaluation_data.logged_evaluation,
        alerted_evaluation=evaluation_data.alerted_evaluation,
        prevented_evaluation=evaluation_data.prevented_evaluation,
        stakeholder_notified_evaluation=evaluation_data.stakeholder_notified_evaluation,
        activity_coverage_score=evaluation_data.activity_coverage_score,
        event_to_alert_data=evaluation_data.event_to_alert_data,
        event_to_alert_evaluation_result=evaluation_data.event_to_alert_evaluation_result,
        alert_to_stakeholder_data=evaluation_data.alert_to_stakeholder_data,
        alert_to_stakeholder_evaluation_result=evaluation_data.alert_to_stakeholder_evaluation_result,
        alert_severity_data=evaluation_data.alert_severity_data,
        alert_severity_evaluation_result=evaluation_data.alert_severity_evaluation_result,
        stakeholder_notification_severity_data=evaluation_data.stakeholder_notification_severity_data,
        stakeholder_notification_severity_evaluation_result=evaluation_data.stakeholder_notification_severity_evaluation_result,
    )
    session.add(evaluation)
    session.flush()

    for dq in evaluation_data.dynamic_questions:
        template_id = template_name_map.get(dq.evaluation_template_name)
        if template_id is None:
            warnings.append(
                f"EvaluationTemplate '{dq.evaluation_template_name}' not found — "
                f"dynamic question dropped."
            )
            continue
        session.add(
            ActivityEvaluationDynamicQuestions(
                activity_evaluation_id=evaluation.id,
                evaluation_template_id=template_id,
                data=dq.data,
                evaluation_result=dq.evaluation_result,
                position=dq.position,
            )
        )


def _link_activity_assets(
    activity_id: uuid.UUID,
    asset_names: list[str],
    role: str,
    asset_name_map: dict[str, uuid.UUID],
    session: Session,
) -> None:
    """
    Insert activity_asset association rows for a given role.
    """
    for name in asset_names:
        asset_id = asset_name_map.get(name)
        if asset_id is None:
            continue
        session.execute(
            insert(activity_asset_association).values(
                activity_id=activity_id,
                asset_id=asset_id,
                role=role,
            )
        )


def _import_activity(
    activity_data: ActivityExport,
    assessment_id: uuid.UUID,
    group_id: uuid.UUID,
    user: User,
    tag_name_map: dict[str, uuid.UUID],
    asset_name_map: dict[str, uuid.UUID],
    template_name_map: dict[str, uuid.UUID],
    warnings: list[str],
    zf: zipfile.ZipFile,
    session: Session,
    activity_id_map: dict[str, str],
    file_id_map: dict[str, str],
) -> None:
    """
    Create a single activity with all associations and children.
    Populates activity_id_map and file_id_map with old→new UUID mappings.
    """
    activity = Activity(
        assessment_id=assessment_id,
        activity_group_id=group_id,
        created_by=user.id,
        name=activity_data.name,
        mitre_tactic=activity_data.mitre_tactic,
        mitre_technique=activity_data.mitre_technique,
        provider=activity_data.provider,
        priority=activity_data.priority,
        visible=activity_data.visible,
        activity_position=activity_data.activity_position,
        state=activity_data.state,
        activity_rationale=activity_data.activity_rationale,
        activity_actions=activity_data.activity_actions,
        activity_requirements=activity_data.activity_requirements,
        activity_notes=activity_data.activity_notes,
        activity_start_time=activity_data.activity_start_time,
        activity_end_time=activity_data.activity_end_time,
        expected_logging=activity_data.expected_logging,
        expected_prevention=activity_data.expected_prevention,
        expected_alert_creation=activity_data.expected_alert_creation,
        expected_stakeholder_notification=activity_data.expected_stakeholder_notification,
        expected_severity=activity_data.expected_severity,
        logged=activity_data.logged,
        log_time=activity_data.log_time,
        prevented=activity_data.prevented,
        prevent_time=activity_data.prevent_time,
        alerted=activity_data.alerted,
        alert_severity=activity_data.alert_severity,
        alert_time=activity_data.alert_time,
        stakeholder_notification_created=activity_data.stakeholder_notification_created,
        stakeholder_notification_severity=activity_data.stakeholder_notification_severity,
        stakeholder_notification_time=activity_data.stakeholder_notification_time,
        log_notes=activity_data.log_notes,
        alert_notes=activity_data.alert_notes,
        prevent_notes=activity_data.prevent_notes,
        stakeholder_notification_notes=activity_data.stakeholder_notification_notes,
        linked_knowledge_base_articles=activity_data.linked_knowledge_base_articles,
        deleted=activity_data.deleted,
    )
    session.add(activity)
    session.flush()

    # Track old → new activity ID
    if activity_data.original_id:
        activity_id_map[activity_data.original_id] = str(activity.id)

    # Tag associations
    for tag_name in activity_data.tag_names:
        tag_id = tag_name_map.get(tag_name)
        if tag_id is not None:
            session.execute(
                insert(activity_tag_association).values(
                    activity_id=activity.id,
                    tag_id=tag_id,
                )
            )

    # Asset associations for all roles
    role_mapping: list[tuple[list[str], str]] = [
        (activity_data.source_names, ActivityAssetRole.SOURCE.value),
        (activity_data.target_names, ActivityAssetRole.TARGET.value),
        (activity_data.tool_names, ActivityAssetRole.TOOL.value),
        (activity_data.log_source_names, ActivityAssetRole.LOG_SOURCE.value),
        (
            activity_data.prevention_source_names,
            ActivityAssetRole.PREVENTION_SOURCE.value,
        ),
        (activity_data.alert_source_names, ActivityAssetRole.ALERT_SOURCE.value),
        (
            activity_data.stakeholder_notification_source_names,
            ActivityAssetRole.STAKEHOLDER_NOTIFICATION_SOURCE.value,
        ),
    ]
    for names, role in role_mapping:
        _link_activity_assets(activity.id, names, role, asset_name_map, session)

    # Evaluation
    if activity_data.evaluation is not None:
        _import_evaluation(
            activity.id,
            activity_data.evaluation,
            template_name_map,
            warnings,
            session,
        )

    # Files
    for file_data in activity_data.files:
        file_content = zf.read(file_data.zip_path)
        new_file = File(
            activity_id=activity.id,
            created_by=user.id,
            filename=sanitize_filename(file_data.filename) or "unnamed",
            content_type=file_data.content_type,
            category=file_data.category,
            size=file_data.size,
            file_content=file_content,
        )
        session.add(new_file)
        session.flush()

        # Track old → new file ID
        if file_data.original_id:
            file_id_map[file_data.original_id] = str(new_file.id)


def _rewrite_text(
    text: str,
    new_assessment_id: str,
    old_assessment_id: str,
    activity_id_map: dict[str, str],
    file_id_map: dict[str, str],
) -> str:
    """
    Replace old assessment/activity/file UUIDs in a text string with new ones.
    """

    def _replace_url(match: re.Match) -> str:
        old_aid = match.group("assessment_id")
        old_act = match.group("activity_id")
        old_fid = match.group("file_id")

        new_aid = new_assessment_id if old_aid == old_assessment_id else old_aid
        new_act = activity_id_map.get(old_act, old_act)
        new_fid = file_id_map.get(old_fid, old_fid)

        return (
            f"/api/v1/assessments/{new_aid}/activity/{new_act}/files/{new_fid}/download"
        )

    return _FILE_URL_RE.sub(_replace_url, text)


def _rewrite_fields(
    obj: object,
    fields: list[str],
    new_assessment_id: str,
    old_assessment_id: str,
    activity_id_map: dict[str, str],
    file_id_map: dict[str, str],
) -> bool:
    """
    Rewrite embedded file URLs in the given fields of an ORM object.
    Returns True if any field was changed.
    """
    changed = False
    for field in fields:
        value = getattr(obj, field)
        if not value or not isinstance(value, str):
            continue
        new_value = _rewrite_text(
            value, new_assessment_id, old_assessment_id, activity_id_map, file_id_map
        )
        if new_value != value:
            setattr(obj, field, new_value)
            changed = True
    return changed


def _rewrite_embedded_urls(
    assessment_id: uuid.UUID,
    old_assessment_id: str,
    activity_id_map: dict[str, str],
    file_id_map: dict[str, str],
    session: Session,
) -> None:
    """
    Rewrite embedded file URLs in all text fields across Activity,
    ActivityEvaluation, and ActivityEvaluationDynamicQuestions models.
    """
    if not old_assessment_id or (not activity_id_map and not file_id_map):
        return

    new_assessment_id = str(assessment_id)

    activities = (
        session.execute(select(Activity).where(Activity.assessment_id == assessment_id))
        .scalars()
        .unique()
        .all()
    )

    for activity in activities:
        # Rewrite Activity text fields
        if _rewrite_fields(
            activity,
            _ACTIVITY_TEXT_FIELDS,
            new_assessment_id,
            old_assessment_id,
            activity_id_map,
            file_id_map,
        ):
            session.add(activity)

        # Rewrite ActivityEvaluation evidence fields
        if activity.evaluation:
            if _rewrite_fields(
                activity.evaluation,
                _EVALUATION_TEXT_FIELDS,
                new_assessment_id,
                old_assessment_id,
                activity_id_map,
                file_id_map,
            ):
                session.add(activity.evaluation)

            # Rewrite DynamicQuestions data
            for dq in activity.evaluation.dynamic_questions:
                if _rewrite_fields(
                    dq,
                    _DYNAMIC_QUESTION_TEXT_FIELDS,
                    new_assessment_id,
                    old_assessment_id,
                    activity_id_map,
                    file_id_map,
                ):
                    session.add(dq)


def import_assessment_service(
    zip_bytes: bytes,
    user: User,
    session: Session,
) -> ImportResponse:
    """
    Import an assessment from a zip archive.
    Returns an ImportResponse with the new assessment ID, message, and any
    warnings (e.g. dropped EvaluationTemplate references).
    """
    warnings: list[str] = []

    # Parse the zip
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zip file"
        )

    try:
        manifest_bytes = zf.read("manifest.json")
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zip file does not contain manifest.json",
        )

    data = AssessmentExportData.model_validate_json(manifest_bytes)

    if data.format_version != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format version: {data.format_version}",
        )

    # Build evaluation template name → ID map
    template_name_map = _build_eval_template_name_map(session)

    # ID remapping for embedded file URLs
    activity_id_map: dict[str, str] = {}  # old_activity_id → new_activity_id
    file_id_map: dict[str, str] = {}  # old_file_id → new_file_id

    # ── Create Assessment ─────────────────────────────────────────────
    assessment = Assessment(
        name=data.assessment_name,
        description=data.assessment_description,
        assessment_type=data.assessment_type,
        created_by=user.id,
    )

    # Resolve default_evaluation_templates
    resolved_defaults: list[dict] = []
    for det in data.default_evaluation_templates:
        tid = template_name_map.get(det.evaluation_template_name)
        if tid is None:
            warnings.append(
                f"Default EvaluationTemplate '{det.evaluation_template_name}' "
                f"not found — skipped."
            )
            continue
        resolved_defaults.append(
            {"evaluation_template_id": str(tid), "position": det.position}
        )
    assessment.default_evaluation_templates = resolved_defaults

    session.add(assessment)
    session.flush()

    # ── Create Tags ───────────────────────────────────────────────────
    tag_name_map: dict[str, uuid.UUID] = {}
    for tag_data in data.tags:
        tag = Tag(
            name=tag_data.name,
            color=tag_data.color,
            assessment_id=assessment.id,
            created_by=user.id,
        )
        session.add(tag)
        session.flush()
        tag_name_map[tag.name] = tag.id

    # ── Create Assets ─────────────────────────────────────────────────
    asset_name_map: dict[str, uuid.UUID] = {}
    for asset_data in data.assets:
        asset = Asset(
            name=asset_data.name,
            icon=asset_data.icon,
            properties=asset_data.properties or {},
            assessment_id=assessment.id,
            created_by=user.id,
        )
        session.add(asset)
        session.flush()
        asset_name_map[asset.name] = asset.id

    # ── Create Activity Groups + Activities ───────────────────────────
    has_default = any(g.is_default for g in data.activity_groups)

    for group_data in data.activity_groups:
        group = ActivityGroup(
            name=group_data.name,
            assessment_id=assessment.id,
            visible=group_data.visible,
            is_default=group_data.is_default,
            activity_group_position=group_data.activity_group_position,
            deleted=group_data.deleted,
            created_by=user.id,
        )
        session.add(group)
        session.flush()

        for act_data in group_data.activities:
            _import_activity(
                act_data,
                assessment.id,
                group.id,
                user,
                tag_name_map,
                asset_name_map,
                template_name_map,
                warnings,
                zf,
                session,
                activity_id_map,
                file_id_map,
            )

    # Ensure a default group exists if the export didn't have one
    if not has_default:
        get_or_create_default_group(assessment.id, session, created_by=user.id)

    # ── Rewrite embedded file URLs ────────────────────────────────────
    _rewrite_embedded_urls(
        assessment.id,
        data.original_assessment_id,
        activity_id_map,
        file_id_map,
        session,
    )

    session.commit()
    zf.close()
    release_memory()

    return ImportResponse(
        assessment_id=assessment.id,
        message="Assessment imported successfully",
        warnings=warnings,
    )
