import io
import uuid
import zipfile
from datetime import datetime, timezone

from pathvalidate import sanitize_filename
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_group import ActivityGroup
from app.models.asset import Asset
from app.models.evaluation_template import EvaluationTemplate
from app.models.file import File
from app.models.tag import Tag
from app.models.user import User
from app.schemas.assessment_export import (
    ActivityExport,
    ActivityGroupExport,
    AssessmentExportData,
    AssetExport,
    DefaultEvaluationTemplateExport,
    DynamicQuestionExport,
    EvaluationExport,
    FileExport,
    TagExport,
)
from app.services.assessment.assessment import get_assessment_by_id_service
from app.services.utils.memory import release_memory


def _build_evaluation_template_map(session: Session) -> dict[uuid.UUID, str]:
    """
    Build a mapping of evaluation template ID → name.
    """
    templates = session.execute(select(EvaluationTemplate)).scalars().all()
    return {t.id: t.name for t in templates}


def _export_evaluation(
    evaluation: ActivityEvaluation | None,
    template_map: dict[uuid.UUID, str],
) -> EvaluationExport | None:
    """
    Export an evaluation, including dynamic questions.
    """
    if evaluation is None:
        return None

    dynamic_questions = []
    for dq in evaluation.dynamic_questions:
        template_name = template_map.get(dq.evaluation_template_id)
        if template_name is None:
            continue  # skip if template was deleted
        dynamic_questions.append(
            DynamicQuestionExport(
                evaluation_template_name=template_name,
                data=dq.data,
                evaluation_result=dq.evaluation_result,
                position=dq.position,
            )
        )

    return EvaluationExport(
        logged_evaluation=evaluation.logged_evaluation,
        alerted_evaluation=evaluation.alerted_evaluation,
        prevented_evaluation=evaluation.prevented_evaluation,
        stakeholder_notified_evaluation=evaluation.stakeholder_notified_evaluation,
        activity_coverage_score=evaluation.activity_coverage_score,
        event_to_alert_data=evaluation.event_to_alert_data,
        event_to_alert_evaluation_result=evaluation.event_to_alert_evaluation_result,
        alert_to_stakeholder_data=evaluation.alert_to_stakeholder_data,
        alert_to_stakeholder_evaluation_result=evaluation.alert_to_stakeholder_evaluation_result,
        alert_severity_data=evaluation.alert_severity_data,
        alert_severity_evaluation_result=evaluation.alert_severity_evaluation_result,
        stakeholder_notification_severity_data=evaluation.stakeholder_notification_severity_data,
        stakeholder_notification_severity_evaluation_result=evaluation.stakeholder_notification_severity_evaluation_result,
        dynamic_questions=dynamic_questions,
    )


def _export_activity(
    activity: Activity,
    template_map: dict[uuid.UUID, str],
    zip_file: zipfile.ZipFile,
) -> ActivityExport:
    """
    Export a single activity, writing any file blobs into the zip.
    """
    # Export files
    file_exports: list[FileExport] = []
    for f in activity.files:
        safe_filename = sanitize_filename(f.filename) or "file"
        zip_path = f"files/{f.id}_{safe_filename}"
        zip_file.writestr(zip_path, f.file_content)
        file_exports.append(
            FileExport(
                filename=f.filename,
                content_type=f.content_type,
                category=f.category,
                size=f.size,
                zip_path=zip_path,
                original_id=str(f.id),
            )
        )

    return ActivityExport(
        original_id=str(activity.id),
        name=activity.name,
        mitre_tactic=activity.mitre_tactic,
        mitre_technique=activity.mitre_technique,
        provider=activity.provider,
        priority=activity.priority,
        visible=activity.visible or False,
        activity_position=activity.activity_position or 0,
        state=activity.state,
        activity_rationale=activity.activity_rationale,
        activity_actions=activity.activity_actions,
        activity_requirements=activity.activity_requirements,
        activity_notes=activity.activity_notes,
        activity_start_time=activity.activity_start_time,
        activity_end_time=activity.activity_end_time,
        expected_logging=activity.expected_logging,
        expected_prevention=activity.expected_prevention,
        expected_alert_creation=activity.expected_alert_creation,
        expected_stakeholder_notification=activity.expected_stakeholder_notification,
        expected_severity=activity.expected_severity,
        logged=activity.logged,
        log_time=activity.log_time,
        prevented=activity.prevented,
        prevent_time=activity.prevent_time,
        alerted=activity.alerted,
        alert_severity=activity.alert_severity,
        alert_time=activity.alert_time,
        stakeholder_notification_created=activity.stakeholder_notification_created,
        stakeholder_notification_severity=activity.stakeholder_notification_severity,
        stakeholder_notification_time=activity.stakeholder_notification_time,
        log_notes=activity.log_notes,
        alert_notes=activity.alert_notes,
        prevent_notes=activity.prevent_notes,
        stakeholder_notification_notes=activity.stakeholder_notification_notes,
        linked_knowledge_base_articles=activity.linked_knowledge_base_articles,
        deleted=activity.deleted or False,
        # Associations by name
        tag_names=[t.name for t in activity.tags],
        source_names=[a.name for a in activity.sources],
        target_names=[a.name for a in activity.targets],
        tool_names=[a.name for a in activity.tools],
        log_source_names=[a.name for a in activity.log_sources],
        prevention_source_names=[a.name for a in activity.prevention_sources],
        alert_source_names=[a.name for a in activity.alert_sources],
        stakeholder_notification_source_names=[
            a.name for a in activity.stakeholder_notification_sources
        ],
        # Children
        evaluation=_export_evaluation(activity.evaluation, template_map),
        files=file_exports,
    )


def export_assessment_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> bytes:
    """
    Export an entire assessment as a zip archive.
    Returns the raw bytes of the zip file.
    """
    # ACL check
    assessment = get_assessment_by_id_service(assessment_id, user, session)

    # Evaluation template ID → name mapping
    template_map = _build_evaluation_template_map(session)

    # Load all tags and assets for this assessment
    tags = (
        session.execute(select(Tag).where(Tag.assessment_id == assessment_id))
        .scalars()
        .unique()
        .all()
    )
    assets = (
        session.execute(select(Asset).where(Asset.assessment_id == assessment_id))
        .scalars()
        .unique()
        .all()
    )

    # Load activity groups with activities eagerly loaded
    groups = (
        session.execute(
            select(ActivityGroup)
            .where(ActivityGroup.assessment_id == assessment_id)
            .options(
                selectinload(ActivityGroup.activities)
                .selectinload(Activity.files)
                .undefer(File.file_content)
            )
            .order_by(ActivityGroup.activity_group_position)
        )
        .scalars()
        .unique()
        .all()
    )

    # Resolve default_evaluation_templates names
    default_eval_templates: list[DefaultEvaluationTemplateExport] = []
    for det in assessment.default_evaluation_templates or []:
        tid = det.get("evaluation_template_id")
        if tid and str(tid) != "":
            tname = template_map.get(uuid.UUID(str(tid)))
            if tname:
                default_eval_templates.append(
                    DefaultEvaluationTemplateExport(
                        evaluation_template_name=tname,
                        position=det.get("position", 0),
                    )
                )

    # Build the zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Export groups + activities
        group_exports: list[ActivityGroupExport] = []
        for group in groups:
            activity_exports: list[ActivityExport] = []
            for act in sorted(group.activities, key=lambda a: a.activity_position or 0):
                activity_exports.append(_export_activity(act, template_map, zf))
            group_exports.append(
                ActivityGroupExport(
                    name=group.name,
                    visible=group.visible or False,
                    is_default=group.is_default or False,
                    activity_group_position=group.activity_group_position or 0,
                    deleted=group.deleted or False,
                    activities=activity_exports,
                )
            )

        export_data = AssessmentExportData(
            format_version=1,
            exported_at=datetime.now(timezone.utc),
            original_assessment_id=str(assessment_id),
            assessment_name=assessment.name,
            assessment_description=assessment.description,
            assessment_type=assessment.assessment_type,
            default_evaluation_templates=default_eval_templates,
            tags=[TagExport(name=t.name, color=t.color) for t in tags],
            assets=[
                AssetExport(name=a.name, icon=a.icon, properties=a.properties)
                for a in assets
            ],
            activity_groups=group_exports,
        )

        zf.writestr("manifest.json", export_data.model_dump_json(indent=2))

    buf.seek(0)
    result = buf.getvalue()
    buf.close()
    del buf
    release_memory()
    return result
