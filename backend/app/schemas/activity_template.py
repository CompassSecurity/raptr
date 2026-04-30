import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.enums.enums import ActivityPriority, ActivitySeverity
from app.schemas.general import BaseFilter


class ActivityTemplateBase(BaseModel):
    """
    Activity template base model
    """

    activity_actions: str | None = None
    activity_notes: str | None = None
    activity_rationale: str | None = None
    activity_requirements: str | None = None
    expected_logging: bool | None = None
    expected_alert_creation: bool | None = None
    expected_prevention: bool | None = None
    expected_stakeholder_notification: bool | None = None
    expected_severity: ActivitySeverity | None = None
    mitre_tactic: str
    mitre_technique: str
    name: str
    priority: ActivityPriority | None = None
    provider: str
    linked_knowledge_base_articles: list[str] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Windows: Malicious Link Execution on Client",
                "mitre_tactic": "Execution",
                "mitre_technique": "T1204.001",
                "activity_rationale": "Users or attackers might visit known malicious sites from the system.",
                "activity_actions": "",
                "activity_requirements": "Standard Windows workplace with Internet access.",
                "activity_notes": "",
                "provider": "Compass Security",
                "expected_logging": True,
                "expected_prevention": True,
                "expected_alert_creation": True,
                "expected_stakeholder_notification": False,
                "expected_severity": "Medium",
                "priority": "Medium",
            }
        },
    )


class ActivityTemplateRead(ActivityTemplateBase):
    """
    Template activity read model
    """

    id: uuid.UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **ActivityTemplateBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "00000000-0000-0000-0000-000000000000",
            }
        },
    )


class ActivityTemplateFilter(BaseFilter):
    """
    Filter schema for activity template queries. All fields optional.
    """

    name: str | None = None
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    provider: str | None = None
    priority: list[ActivityPriority] | None = None
    sort_by: (
        Literal["name", "mitre_tactic", "mitre_technique", "provider", "priority"]
        | None
    ) = None
