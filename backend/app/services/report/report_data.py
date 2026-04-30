"""
Report data layer — assembles ReportContext from assessment data.

This is the "middle layer" between the database and the Jinja2 rendering engine.
It fetches all assessment data, resolves names, and computes statistics.
"""

import base64
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, undefer

from app.enums.enums import FileType
from app.models.activity import Activity
from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.file import File
from app.models.mitre import Tactic, Technique
from app.models.user import User
from app.services.statistics.assessment_statistics import (
    get_assessment_statistics_service,
)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FileReport:
    id: str
    filename: str
    content_type: str  # MIME type string, e.g. "image/png"
    size: int
    category: str  # "red" or "blue"
    data_base64: str  # base64-encoded file content


@dataclass
class DynamicQuestionReport:
    question: str
    description: str
    data: str | None
    result: str  # "pass", "fail", "n/a"
    position: int


@dataclass
class ActivityReport:
    # Identity
    id: str
    name: str
    position: int
    group_name: str
    group_position: int

    # MITRE
    mitre_tactic: str
    mitre_technique: str
    mitre_tactic_name: str
    mitre_technique_name: str

    # Metadata
    provider: str | None
    priority: str | None
    state: str | None
    visible: bool

    # Timing
    start_time: datetime | None
    end_time: datetime | None

    # Details (markdown fields)
    rationale: str | None
    actions: str | None
    requirements: str | None
    notes: str | None

    # Expected results
    expected_logging: bool | None
    expected_prevention: bool | None
    expected_alert_creation: bool | None
    expected_stakeholder_notification: bool | None
    expected_severity: str | None

    # Actual results
    logged: bool | None
    log_time: datetime | None
    prevented: bool | None
    prevent_time: datetime | None
    alerted: bool | None
    alert_severity: str | None
    alert_time: datetime | None
    stakeholder_notified: bool | None
    stakeholder_notification_severity: str | None
    stakeholder_notification_time: datetime | None

    # Detection notes (markdown fields)
    log_notes: str | None
    alert_notes: str | None
    prevent_notes: str | None
    stakeholder_notification_notes: str | None

    # Related entities (resolved)
    tags: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    targets: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    log_sources: list[dict[str, Any]] = field(default_factory=list)
    prevention_sources: list[dict[str, Any]] = field(default_factory=list)
    alert_sources: list[dict[str, Any]] = field(default_factory=list)
    stakeholder_notification_sources: list[dict[str, Any]] = field(default_factory=list)

    # Evaluation
    coverage_score: int | None = None
    logged_evaluation: str | None = None
    alerted_evaluation: str | None = None
    prevented_evaluation: str | None = None
    stakeholder_notified_evaluation: str | None = None

    # Time-based evaluation
    event_to_alert_data: str | None = None
    event_to_alert_result: str | None = None
    alert_to_stakeholder_data: str | None = None
    alert_to_stakeholder_result: str | None = None

    # Severity-based evaluation
    alert_severity_data: str | None = None
    alert_severity_result: str | None = None
    stakeholder_notification_severity_data: str | None = None
    stakeholder_notification_severity_result: str | None = None

    dynamic_questions: list[DynamicQuestionReport] = field(default_factory=list)

    # Files
    files: list[FileReport] = field(default_factory=list)


@dataclass
class ActivityGroupReport:
    name: str
    position: int
    is_default: bool
    activities: list[ActivityReport] = field(default_factory=list)


@dataclass
class AssessmentInfo:
    id: str
    name: str
    description: str
    assessment_type: str


@dataclass
class ReportContext:
    assessment: AssessmentInfo
    activities_grouped: list[ActivityGroupReport]
    activities_flat: list[ActivityReport]
    statistics: dict[str, Any]
    generated_at: datetime
    generated_by: str
    template_filename: str


# ---------------------------------------------------------------------------
# MITRE name resolution
# ---------------------------------------------------------------------------


def _build_mitre_lookup(session: Session) -> tuple[dict[str, str], dict[str, str]]:
    """Build mitre_id -> name lookup dicts for tactics and techniques."""
    tactics = session.execute(select(Tactic)).scalars().all()
    techniques = session.execute(select(Technique)).scalars().all()

    tactic_names = {t.mitre_id: t.name for t in tactics}
    # Also map by name for activities that store tactic name instead of ID
    for t in tactics:
        tactic_names[t.name] = t.name

    technique_names = {t.mitre_id: t.name for t in techniques}
    for t in techniques:
        technique_names[t.name] = t.name

    return tactic_names, technique_names


# ---------------------------------------------------------------------------
# Activity -> ActivityReport conversion
# ---------------------------------------------------------------------------


def _build_activity_report(
    activity: Activity,
    group_name: str,
    group_position: int,
    tactic_names: dict[str, str],
    technique_names: dict[str, str],
) -> ActivityReport:
    """Convert a SQLAlchemy Activity to an ActivityReport dataclass."""
    # Evaluation data
    eval_ = activity.evaluation
    coverage_score = None
    logged_eval = None
    alerted_eval = None
    prevented_eval = None
    stakeholder_eval = None
    event_to_alert_data = None
    event_to_alert_result = None
    alert_to_stakeholder_data = None
    alert_to_stakeholder_result = None
    alert_severity_data = None
    alert_severity_result = None
    sn_severity_data = None
    sn_severity_result = None
    dq_reports: list[DynamicQuestionReport] = []

    if eval_:
        coverage_score = eval_.activity_coverage_score
        logged_eval = eval_.logged_evaluation.value if eval_.logged_evaluation else None
        alerted_eval = (
            eval_.alerted_evaluation.value if eval_.alerted_evaluation else None
        )
        prevented_eval = (
            eval_.prevented_evaluation.value if eval_.prevented_evaluation else None
        )
        stakeholder_eval = (
            eval_.stakeholder_notified_evaluation.value
            if eval_.stakeholder_notified_evaluation
            else None
        )

        event_to_alert_data = eval_.event_to_alert_data or None
        event_to_alert_result = (
            eval_.event_to_alert_evaluation_result.value
            if eval_.event_to_alert_evaluation_result
            else None
        )
        alert_to_stakeholder_data = eval_.alert_to_stakeholder_data or None
        alert_to_stakeholder_result = (
            eval_.alert_to_stakeholder_evaluation_result.value
            if eval_.alert_to_stakeholder_evaluation_result
            else None
        )
        alert_severity_data = eval_.alert_severity_data or None
        alert_severity_result = (
            eval_.alert_severity_evaluation_result.value
            if eval_.alert_severity_evaluation_result
            else None
        )
        sn_severity_data = eval_.stakeholder_notification_severity_data or None
        sn_severity_result = (
            eval_.stakeholder_notification_severity_evaluation_result.value
            if eval_.stakeholder_notification_severity_evaluation_result
            else None
        )

        for dq in eval_.dynamic_questions:
            template = dq.evaluation_template
            dq_reports.append(
                DynamicQuestionReport(
                    question=template.evaluation_criteria if template else "",
                    description=template.description if template else "",
                    data=dq.data or None,
                    result=dq.evaluation_result.value
                    if dq.evaluation_result
                    else "n/a",
                    position=dq.position,
                )
            )

    return ActivityReport(
        id=str(activity.id),
        name=activity.name,
        position=activity.activity_position,
        group_name=group_name,
        group_position=group_position,
        mitre_tactic=activity.mitre_tactic,
        mitre_technique=activity.mitre_technique,
        mitre_tactic_name=tactic_names.get(
            activity.mitre_tactic, activity.mitre_tactic
        ),
        mitre_technique_name=technique_names.get(
            activity.mitre_technique, activity.mitre_technique
        ),
        provider=activity.provider,
        priority=activity.priority.value if activity.priority else None,
        state=activity.state.value if activity.state else None,
        visible=activity.visible or False,
        start_time=activity.activity_start_time,
        end_time=activity.activity_end_time,
        rationale=activity.activity_rationale,
        actions=activity.activity_actions,
        requirements=activity.activity_requirements,
        notes=activity.activity_notes,
        expected_logging=activity.expected_logging,
        expected_prevention=activity.expected_prevention,
        expected_alert_creation=activity.expected_alert_creation,
        expected_stakeholder_notification=activity.expected_stakeholder_notification,
        expected_severity=activity.expected_severity.value
        if activity.expected_severity
        else None,
        logged=activity.logged,
        log_time=activity.log_time,
        prevented=activity.prevented,
        prevent_time=activity.prevent_time,
        alerted=activity.alerted,
        alert_severity=activity.alert_severity,
        alert_time=activity.alert_time,
        stakeholder_notified=activity.stakeholder_notification_created,
        stakeholder_notification_severity=activity.stakeholder_notification_severity,
        stakeholder_notification_time=activity.stakeholder_notification_time,
        log_notes=activity.log_notes,
        alert_notes=activity.alert_notes,
        prevent_notes=activity.prevent_notes,
        stakeholder_notification_notes=activity.stakeholder_notification_notes,
        tags=[
            {"name": t.name, "color": t.color} for t in activity.tags if not t.deleted
        ],
        sources=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.sources
            if not a.deleted
        ],
        targets=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.targets
            if not a.deleted
        ],
        tools=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.tools
            if not a.deleted
        ],
        log_sources=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.log_sources
            if not a.deleted
        ],
        prevention_sources=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.prevention_sources
            if not a.deleted
        ],
        alert_sources=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.alert_sources
            if not a.deleted
        ],
        stakeholder_notification_sources=[
            {"name": a.name, "icon": a.icon, "properties": a.properties}
            for a in activity.stakeholder_notification_sources
            if not a.deleted
        ],
        coverage_score=coverage_score,
        logged_evaluation=logged_eval,
        alerted_evaluation=alerted_eval,
        prevented_evaluation=prevented_eval,
        stakeholder_notified_evaluation=stakeholder_eval,
        event_to_alert_data=event_to_alert_data,
        event_to_alert_result=event_to_alert_result,
        alert_to_stakeholder_data=alert_to_stakeholder_data,
        alert_to_stakeholder_result=alert_to_stakeholder_result,
        alert_severity_data=alert_severity_data,
        alert_severity_result=alert_severity_result,
        stakeholder_notification_severity_data=sn_severity_data,
        stakeholder_notification_severity_result=sn_severity_result,
        dynamic_questions=dq_reports,
        files=[
            FileReport(
                id=str(f.id),
                filename=f.filename,
                content_type=f.content_type.value,
                size=f.size,
                category=f.category.value,
                data_base64=base64.b64encode(f.file_content).decode("ascii"),
            )
            for f in activity.files
        ],
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build_report_context(
    assessment_id: uuid.UUID,
    template_filename: str,
    session: Session,
    user: User,
    sort_by: str = "activity_position",
    sort_order: str = "asc",
) -> ReportContext:
    """
    Build the full ReportContext for an assessment.

    Fetches all non-deleted activity groups and activities,
    resolves MITRE names, computes statistics, and returns
    a context dict ready for Jinja2 rendering.
    """
    # 1. Fetch assessment
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # 2. Build MITRE lookups
    tactic_names, technique_names = _build_mitre_lookup(session)

    # 3. Fetch non-deleted activity groups sorted by position
    groups = (
        session.execute(
            select(ActivityGroup)
            .where(ActivityGroup.assessment_id == assessment_id)
            .where(ActivityGroup.deleted == False)  # noqa: E712
            .order_by(ActivityGroup.activity_group_position.asc())
        )
        .scalars()
        .all()
    )

    # 4. Fetch non-deleted activities
    activities_stmt = (
        select(Activity)
        .where(Activity.assessment_id == assessment_id)
        .where(Activity.deleted == False)  # noqa: E712
        .options(selectinload(Activity.files).undefer(File.file_content))
    )
    activities = session.execute(activities_stmt).scalars().unique().all()

    # Index activities by group
    activities_by_group: dict[uuid.UUID, list[Activity]] = {}
    for act in activities:
        gid = act.activity_group_id
        if gid not in activities_by_group:
            activities_by_group[gid] = []
        activities_by_group[gid].append(act)

    # Sort activities within each group by position
    for gid in activities_by_group:
        activities_by_group[gid].sort(key=lambda a: a.activity_position)

    # 5. Build grouped view
    grouped: list[ActivityGroupReport] = []
    all_reports: list[ActivityReport] = []

    for group in groups:
        group_activities = activities_by_group.get(group.id, [])
        reports = [
            _build_activity_report(
                a,
                group.name,
                group.activity_group_position,
                tactic_names,
                technique_names,
            )
            for a in group_activities
        ]
        all_reports.extend(reports)

        grouped.append(
            ActivityGroupReport(
                name=group.name,
                position=group.activity_group_position,
                is_default=group.is_default,
                activities=reports,
            )
        )

    # 6. Build flat sorted view
    sort_key = _get_sort_key(sort_by)
    reverse = sort_order == "desc"
    flat = sorted(all_reports, key=sort_key, reverse=reverse)

    # 7. Compute statistics (reuse the assessment statistics service)
    statistics = get_assessment_statistics_service(assessment_id, session).model_dump()

    # 8. Build context
    return ReportContext(
        assessment=AssessmentInfo(
            id=str(assessment.id),
            name=assessment.name,
            description=assessment.description,
            assessment_type=assessment.assessment_type.value,
        ),
        activities_grouped=grouped,
        activities_flat=flat,
        statistics=statistics,
        generated_at=datetime.now(),
        generated_by=user.email,
        template_filename=template_filename,
    )


def _get_sort_key(sort_by: str):
    """Return a sort key function for ActivityReport based on field name."""
    SORT_FIELDS = {
        "activity_position": lambda a: (a.group_position, a.position, a.name),
        "name": lambda a: a.name.lower(),
        "mitre_tactic": lambda a: (a.mitre_tactic, a.mitre_technique),
        "priority": lambda a: _priority_order(a.priority),
        "state": lambda a: a.state or "",
        "start_time": lambda a: a.start_time or datetime.min,
        "coverage_score": lambda a: (
            a.coverage_score if a.coverage_score is not None else -1
        ),
    }
    return SORT_FIELDS.get(sort_by, SORT_FIELDS["activity_position"])


def _priority_order(priority: str | None) -> int:
    """Map priority to sort order (Critical=0, Low=3, None=4)."""
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return order.get(priority or "", 4)


# ---------------------------------------------------------------------------
# Image data collection for rendering
# ---------------------------------------------------------------------------


def collect_report_images(
    session: Session, assessment_id: uuid.UUID
) -> dict[str, tuple[str, bytes]]:
    """
    Collect all image files for an assessment as a lookup dict.

    Returns a dict of file_id -> (content_type, raw_bytes) for image files.
    Used by render functions to embed images in HTML (base64 data URIs)
    and DOCX (InlineImage) output.
    """
    image_types = [FileType.PNG, FileType.JPEG, FileType.JPG]
    files = (
        session.execute(
            select(File)
            .join(Activity)
            .where(Activity.assessment_id == assessment_id)
            .where(Activity.deleted == False)  # noqa: E712
            .where(File.content_type.in_(image_types))
            .options(undefer(File.file_content))
        )
        .scalars()
        .all()
    )

    return {str(f.id): (f.content_type.value, f.file_content) for f in files}
