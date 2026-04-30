import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.general import BaseFilter


class KnowledgeBaseBase(BaseModel):
    """
    Knowledge Base Base Schema
    """

    name: str
    mitre_technique_id: str | None = None
    content: Any | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "LSASS Dumping",
                "mitre_technique_id": "T1003.001",
                "content": {
                    "sections": [
                        {
                            "title": "Local Execution",
                            "content": "Attackers may dump LSASS locally...",
                            "tabs": [
                                {
                                    "title": "Task Manager",
                                    "content": "Create dump file via Task Manager...",
                                },
                                {
                                    "title": "Mimikatz",
                                    "content": "sekurlsa::logonPasswords",
                                },
                            ],
                        }
                    ]
                },
            }
        }
    )


class KnowledgeBaseRead(KnowledgeBaseBase):
    """
    Knowledge Base Read Schema
    """

    id: uuid.UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **KnowledgeBaseBase.model_config.get("json_schema_extra", {}).get(
                    "example", {}
                ),
                "id": "123e4567-e89b-12d3-a456-426614174000",
            }
        },
    )


class KnowledgeBaseFilter(BaseFilter):
    """
    Knowledge Base Filter Schema
    """

    mitre_technique_id: str | None = None
    names: list[str] | None = None
    sort_by: Literal["name", "mitre_technique_id"] | None = None
