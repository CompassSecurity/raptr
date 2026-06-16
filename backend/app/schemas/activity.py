import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.enums.enums import (
    ActivityPriority,
    ActivitySeverity,
    ActivityState,
    ActivityStateBlue,
)
from app.schemas.activity_evaluation import (
    ActivityEvaluationRead,
    ActivityEvaluationUpdate,
)
from app.schemas.activity_group import ActivityGroupRead
from app.schemas.asset import AssetRead
from app.schemas.general import BaseFilter
from app.schemas.tag import TagRead


class ActivityFilter(BaseFilter):
    """
    Filter schema for activity queries. All fields optional.
    """

    name: str | None = None
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    priority: list[ActivityPriority] | None = None
    state: list[ActivityState] | None = None
    visible: bool | None = None
    deleted: bool | None = None
    tags: list[uuid.UUID] | None = None
    activity_group_id: uuid.UUID | None = None
    sort_by: (
        Literal[
            "name",
            "activity_position",
            "mitre_tactic",
            "mitre_technique",
            "priority",
            "state",
            "visible",
            "created_at",
            "updated_at",
            "activity_group.name",
            "activity_coverage_score",
            "activity_start_time",
            "activity_end_time",
            "tags",
        ]
        | None
    ) = None


class ActivityBase(BaseModel):
    """
    Assessment activity base model
    """

    name: str
    mitre_tactic: str
    mitre_technique: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Windows: Malicious Link Execution on Client",
                "mitre_tactic": "TA0002",
                "mitre_technique": "T1204.001",
            }
        },
    )


class ActivityUpdate(ActivityBase):
    """
    Assessment activity update model
    """

    # Basic information
    provider: str | None = None
    visible: bool = False
    priority: ActivityPriority | None = None
    state: ActivityState | None
    tags: list[uuid.UUID] = []
    activity_group_id: uuid.UUID | None = None

    # Track changes for optimistic concurrency control
    updated_at: datetime | None = None

    # Activity details
    activity_rationale: str | None = None
    activity_actions: str | None = None
    activity_requirements: str | None = None
    activity_notes: str | None = None
    activity_start_time: datetime | None = None
    activity_end_time: datetime | None = None
    sources: list[uuid.UUID] = []
    targets: list[uuid.UUID] = []
    tools: list[uuid.UUID] = []

    # Expected results
    expected_logging: bool | None = None
    expected_prevention: bool | None = None
    expected_alert_creation: bool | None = None
    expected_stakeholder_notification: bool | None = None
    expected_severity: ActivitySeverity | None = None
    log_sources: list[uuid.UUID] = []
    prevention_sources: list[uuid.UUID] = []
    alert_sources: list[uuid.UUID] = []
    stakeholder_notification_sources: list[uuid.UUID] = []

    # Actual results
    logged: bool | None = None
    log_time: datetime | None = None

    prevented: bool | None = None
    prevent_time: datetime | None = None

    alerted: bool | None = None
    alert_severity: ActivitySeverity | None = None
    alert_time: datetime | None = None

    stakeholder_notification_created: bool | None = None
    stakeholder_notification_severity: ActivitySeverity | None = None
    stakeholder_notification_time: datetime | None = None

    # Knowledge Base
    linked_knowledge_base_articles: list[str] | None = None

    # Detection Notes
    log_notes: str | None = None
    alert_notes: str | None = None
    prevent_notes: str | None = None
    stakeholder_notification_notes: str | None = None

    # Evaluation
    evaluation: ActivityEvaluationUpdate | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Windows: Malicious Link Execution on Client",
                "mitre_tactic": "TA0002",
                "mitre_technique": "T1204.001",
                "activity_group_id": "00000000-0000-0000-0000-000000000000",
                "activity_rationale": "Users or attackers might visit known malicious sites from the system.",
                "activity_actions": "",
                "activity_requirements": "Standard Windows workplace with Internet access.",
                "activity_notes": "",
                "provider": "Compass Security",
                "expected_prevention": True,
                "expected_alert_creation": True,
                "expected_stakeholder_notification": False,
                "expected_severity": "Medium",
                "priority": "Medium",
                "visible": False,
                "state": "Pending",
                "activity_start_time": "2026-01-01T10:00:00Z",
                "activity_end_time": "2026-01-01T11:00:00Z",
                "activity_sources": "",
                "activity_targets": "",
                "activity_tools": "",
                "logged": False,
                "prevented": False,
                "prevent_time": "2026-01-01T10:30:00Z",
                "alerted": False,
                "alert_severity": "Low",
                "alert_time": "2026-01-01T10:35:00Z",
                "stakeholder_notification_created": False,
                "stakeholder_notification_severity": "Low",
                "stakeholder_notification_time": "2026-01-01T10:40:00Z",
                "log_notes": "",
                "alert_notes": "",
                "prevent_notes": "",
                "stakeholder_notification_notes": "",
                "tags": ["11111111-1111-1111-1111-111111111111"],
                "sources": [
                    "22222222-2222-2222-2222-222222222222",
                    "22222222-2222-2222-2222-333333333333",
                ],
                "targets": ["33333333-3333-3333-3333-333333333333"],
                "tools": ["44444444-4444-4444-4444-444444444444"],
                "log_sources": ["55555555-5555-5555-5555-555555555555"],
                "prevention_sources": ["66666666-6666-6666-6666-666666666666"],
                "alert_sources": ["77777777-7777-7777-7777-777777777777"],
                "stakeholder_notification_sources": [
                    "88888888-8888-8888-8888-888888888888"
                ],
                "linked_knowledge_base_articles": [
                    "88888888-8888-8888-8888-888888888888"
                ],
                "evaluation": {
                    "logged_evaluation": True,
                    "alerted_evaluation": True,
                    "prevented_evaluation": True,
                    "stakeholder_notified_evaluation": True,
                    "activity_coverage_score": 100,
                    "event_to_alert_data": "2026-01-01T10:00:00Z",
                    "event_to_alert_applicable": True,
                    "event_to_alert_evaluation": True,
                    "alert_to_stakeholder_data": "2026-01-01T10:00:00Z",
                    "alert_to_stakeholder_applicable": True,
                    "alert_to_stakeholder_evaluation": True,
                    "alert_severity_data": "2026-01-01T10:00:00Z",
                    "alert_severity_applicable": True,
                    "alert_severity_evaluation": True,
                    "stakeholder_notification_severity_data": "2026-01-01T10:00:00Z",
                    "stakeholder_notification_severity_applicable": True,
                    "stakeholder_notification_severity_evaluation": True,
                    "dynamic_questions": [
                        {
                            "data": "Dynamic question data",
                            "applicable": True,
                            "evaluation": True,
                            "position": 1,
                            "evaluation_template_id": "00000000-0000-0000-0000-000000000000",
                        }
                    ],
                },
            }
        }
    )


class ActivityRead(ActivityUpdate):
    """
    Assessment activity read model
    """

    id: uuid.UUID
    deleted: bool
    activity_position: int | None = None
    tags: list[TagRead] = []
    sources: list[AssetRead] = []
    targets: list[AssetRead] = []
    tools: list[AssetRead] = []
    log_sources: list[AssetRead] = []
    prevention_sources: list[AssetRead] = []
    alert_sources: list[AssetRead] = []
    stakeholder_notification_sources: list[AssetRead] = []
    linked_knowledge_base_articles: list[str] | None = None
    evaluation: ActivityEvaluationRead | None = None
    activity_group: ActivityGroupRead | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **ActivityUpdate.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
                "deleted": False,
                "activity_position": 1,
            }
        },
    )


class ActivityUpdateBlue(BaseModel):
    """
    Assessment activity update model for Blue users.
    Only allows updating specific fields.
    """

    log_notes: str | None = None
    alert_notes: str | None = None
    prevent_notes: str | None = None
    stakeholder_notification_notes: str | None = None
    logged: bool | None = None
    log_time: datetime | None = None
    prevented: bool | None = None
    prevent_time: datetime | None = None
    alerted: bool | None = None
    alert_severity: ActivitySeverity | None = None
    alert_time: datetime | None = None
    stakeholder_notification_created: bool | None = None
    stakeholder_notification_severity: ActivitySeverity | None = None
    stakeholder_notification_time: datetime | None = None
    state: ActivityStateBlue | None
    log_sources: list[uuid.UUID] | None = None
    prevention_sources: list[uuid.UUID] | None = None
    alert_sources: list[uuid.UUID] | None = None
    stakeholder_notification_sources: list[uuid.UUID] | None = None
    tags: list[uuid.UUID] | None = None
    updated_at: datetime | None = None
