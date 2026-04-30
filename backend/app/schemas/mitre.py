import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MitreFilter(BaseModel):
    """
    Filter schema for mitre queries.
    Inherits from BaseModel because it is not paginated.
    """

    name: str | None = None
    mitre_id: str | None = None
    sort_by: Literal["name", "mitre_id"] | None = None
    sort_order: Literal["asc", "desc"] | None = None


class TacticBase(BaseModel):
    """
    Shared properties for multiple tactic schemas
    """

    id: uuid.UUID
    mitre_id: str
    name: str
    url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
                "mitre_id": "T1001",
                "name": "Data from local system",
                "url": "https://attack.mitre.org/techniques/T1001",
            }
        }
    )


class TechniqueBase(BaseModel):
    """
    Shared properties for multiple technique schemas
    """

    id: uuid.UUID
    mitre_id: str
    name: str
    url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
                "mitre_id": "T1001",
                "name": "Data from local system",
                "url": "https://attack.mitre.org/techniques/T1001",
            }
        }
    )


class TacticWithTechniques(TacticBase):
    """
    Properties of a tactic with its associated techniques
    """

    techniques: list[TechniqueBase]


class TechniqueWithTactics(TechniqueBase):
    """
    Properties of a technique with its associated tactics
    """

    tactics: list[TacticBase]
