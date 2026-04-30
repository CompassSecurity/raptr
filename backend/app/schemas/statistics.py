from pydantic import BaseModel


class StateDistributionItem(BaseModel):
    state: str
    count: int


class PriorityBreakdownItem(BaseModel):
    priority: str
    count: int


class PriorityAverageScoreItem(BaseModel):
    priority: str
    average_score: float | None


class MitreTechniqueScoreItem(BaseModel):
    technique: str
    overall_score: float | None

    expected_logged_score: float | None
    logged_score: float | None

    expected_prevented_score: float | None
    prevented_score: float | None

    expected_alerted_score: float | None
    alerted_score: float | None

    expected_stakeholder_notified_score: float | None
    stakeholder_notified_score: float | None


class MitreOverallTacticScoreItem(BaseModel):
    tactic: str
    overall_score: float | None

    expected_logged_score: float | None
    logged_score: float | None

    expected_prevented_score: float | None
    prevented_score: float | None

    expected_alerted_score: float | None
    alerted_score: float | None

    expected_stakeholder_notified_score: float | None
    stakeholder_notified_score: float | None


class MitreTacticScoreItem(BaseModel):
    tactic: str
    techniques: list[MitreTechniqueScoreItem]


class MeanTimeMetricsItem(BaseModel):
    priority: str
    mean_time_to_detect_seconds: float | None
    mean_time_to_respond_seconds: float | None


class SeverityAccuracyItem(BaseModel):
    expected_severity: str
    actual_informational: int
    actual_low: int
    actual_medium: int
    actual_high: int
    actual_critical: int
    actual_none: int


class AssessmentStatisticsResponse(BaseModel):
    state_distribution: list[StateDistributionItem]
    priority_breakdown: list[PriorityBreakdownItem]
    average_coverage_score: float | None = None
    average_coverage_scores_by_priority: list[PriorityAverageScoreItem]
    mitre_overall_tactic_scores: list[MitreOverallTacticScoreItem]
    mitre_tactic_scores: list[MitreTacticScoreItem]
    mean_time_metrics: list[MeanTimeMetricsItem]
    severity_accuracy: list[SeverityAccuracyItem]
