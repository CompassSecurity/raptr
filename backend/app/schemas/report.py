import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.enums.enums import ReportTemplateFormat


class ReportTemplateBase(BaseModel):
    """
    Base schema for report template
    """

    filename: str
    format: ReportTemplateFormat


class ReportTemplateRead(ReportTemplateBase):
    """
    Schema for reading report template
    """

    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ReportTemplateFilter(BaseModel):
    """
    Schema for filtering report templates
    """

    filename: str | None = None
    format: ReportTemplateFormat | None = None
    sort_by: Literal["filename", "format"] = "filename"
    sort_order: Literal["asc", "desc"] = "asc"


class ReportContextRequest(BaseModel):
    """
    Schema for report context (data layer) request
    """

    sort_by: Literal[
        "activity_position",
        "name",
        "mitre_tactic",
        "priority",
        "state",
        "start_time",
        "coverage_score",
    ] = "activity_position"
    sort_order: Literal["asc", "desc"] = "asc"


class ReportGenerateRequest(ReportContextRequest):
    """
    Schema for report generation request
    """

    template_id: uuid.UUID


class GeneratedReport(BaseModel):
    """
    Schema for generated report
    """

    content: bytes
    media_type: str
    filename: str
