import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.enums import (
    ActivityPriority,
    ActivitySeverity,
    ActivityState,
    AssessmentType,
    EvaluationResult,
    FileCategory,
    FileType,
)

# ── Leaf-level export schemas ────────────────────────────────────────────


class TagExport(BaseModel):
    name: str
    color: str


class AssetExport(BaseModel):
    name: str
    icon: str | None = None
    properties: dict | None = None


class FileExport(BaseModel):
    """
    Reference to a binary file stored in the zip archive.
    """

    filename: str
    content_type: FileType
    category: FileCategory
    size: int
    zip_path: str  # path inside the zip, e.g. "files/abc_screenshot.png"
    original_id: str = ""  # original file UUID for URL rewriting on import


class DynamicQuestionExport(BaseModel):
    evaluation_template_name: str
    data: str = ""
    evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    position: int = 0


class EvaluationExport(BaseModel):
    logged_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    alerted_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    prevented_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    stakeholder_notified_evaluation: EvaluationResult = EvaluationResult.NOT_APPLICABLE
    activity_coverage_score: int = 0

    event_to_alert_data: str = ""
    event_to_alert_evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE

    alert_to_stakeholder_data: str = ""
    alert_to_stakeholder_evaluation_result: EvaluationResult = (
        EvaluationResult.NOT_APPLICABLE
    )

    alert_severity_data: str = ""
    alert_severity_evaluation_result: EvaluationResult = EvaluationResult.NOT_APPLICABLE

    stakeholder_notification_severity_data: str = ""
    stakeholder_notification_severity_evaluation_result: EvaluationResult = (
        EvaluationResult.NOT_APPLICABLE
    )

    dynamic_questions: list[DynamicQuestionExport] = []


# ── Activity export ──────────────────────────────────────────────────────


class ActivityExport(BaseModel):
    original_id: str = ""  # original activity UUID for URL rewriting on import
    name: str
    mitre_tactic: str
    mitre_technique: str
    provider: str | None = None
    priority: ActivityPriority | None = None
    visible: bool = False
    activity_position: int = 0
    state: ActivityState | None = None

    # Activity detail fields
    activity_rationale: str | None = None
    activity_actions: str | None = None
    activity_requirements: str | None = None
    activity_notes: str | None = None
    activity_start_time: datetime | None = None
    activity_end_time: datetime | None = None

    # Expected results
    expected_logging: bool | None = None
    expected_prevention: bool | None = None
    expected_alert_creation: bool | None = None
    expected_stakeholder_notification: bool | None = None
    expected_severity: ActivitySeverity | None = None

    # Actual results
    logged: bool | None = None
    log_time: datetime | None = None
    prevented: bool | None = None
    prevent_time: datetime | None = None
    alerted: bool | None = None
    alert_severity: str | None = None
    alert_time: datetime | None = None
    stakeholder_notification_created: bool | None = None
    stakeholder_notification_severity: str | None = None
    stakeholder_notification_time: datetime | None = None

    # Detection notes
    log_notes: str | None = None
    alert_notes: str | None = None
    prevent_notes: str | None = None
    stakeholder_notification_notes: str | None = None

    # Knowledge Base
    linked_knowledge_base_articles: list[str] | None = None

    # Associations by name
    tag_names: list[str] = []
    source_names: list[str] = []
    target_names: list[str] = []
    tool_names: list[str] = []
    log_source_names: list[str] = []
    prevention_source_names: list[str] = []
    alert_source_names: list[str] = []
    stakeholder_notification_source_names: list[str] = []

    # Nested children
    evaluation: EvaluationExport | None = None
    files: list[FileExport] = []

    # Soft-delete state
    deleted: bool = False


# ── Activity Group export ────────────────────────────────────────────────


class ActivityGroupExport(BaseModel):
    name: str
    visible: bool = False
    is_default: bool = False
    activity_group_position: int = 0
    deleted: bool = False
    activities: list[ActivityExport] = []


# ── Top-level envelope ───────────────────────────────────────────────────


class DefaultEvaluationTemplateExport(BaseModel):
    evaluation_template_name: str
    position: int


class AssessmentExportData(BaseModel):
    format_version: int = 1
    exported_at: datetime
    original_assessment_id: str = ""  # original assessment UUID for URL rewriting
    assessment_name: str
    assessment_description: str
    assessment_type: AssessmentType
    default_evaluation_templates: list[DefaultEvaluationTemplateExport] = []
    tags: list[TagExport] = []
    assets: list[AssetExport] = []
    activity_groups: list[ActivityGroupExport] = []

    model_config = ConfigDict(ser_json_timedelta="float")


# ── Import response ─────────────────────────────────────────────────────


class ImportResponse(BaseModel):
    assessment_id: uuid.UUID
    message: str
    warnings: list[str] = []
