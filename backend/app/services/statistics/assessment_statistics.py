import uuid

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.enums.enums import ActivityPriority, ActivityState
from app.models.activity import Activity
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_group import ActivityGroup
from app.models.mitre import Tactic, Technique
from app.schemas.statistics import (
    AssessmentStatisticsResponse,
    MeanTimeMetricsItem,
    MitreOverallTacticScoreItem,
    MitreTacticScoreItem,
    MitreTechniqueScoreItem,
    PriorityAverageScoreItem,
    PriorityBreakdownItem,
    SeverityAccuracyItem,
    StateDistributionItem,
)

# Visibility filter: only visible, non-deleted activities in visible, non-deleted groups.
# Applied consistently for all roles.
_VISIBILITY_FILTERS = [
    Activity.visible.is_(True),
    Activity.deleted.is_(False),
    ActivityGroup.visible.is_(True),
    ActivityGroup.deleted.is_(False),
]


def _get_state_distribution(
    assessment_id: uuid.UUID, session: Session
) -> list[StateDistributionItem]:
    """
    Compute Activity State Distribution.
    """
    state_rows = session.execute(
        select(Activity.state, func.count().label("cnt"))
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(Activity.assessment_id == assessment_id)
        .where(*_VISIBILITY_FILTERS)
        .group_by(Activity.state)
    ).all()

    return [
        StateDistributionItem(
            state=row.state.value if row.state else "None",
            count=row.cnt,
        )
        for row in state_rows
    ]


def _get_priority_breakdown(
    assessment_id: uuid.UUID, session: Session
) -> list[PriorityBreakdownItem]:
    """
    Compute Priority Breakdown for completed activities.
    """
    priority_rows = session.execute(
        select(Activity.priority, func.count().label("cnt"))
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            *_VISIBILITY_FILTERS,
        )
        .group_by(Activity.priority)
    ).all()

    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(
        [
            PriorityBreakdownItem(
                priority=row.priority.value if row.priority else "None",
                count=row.cnt,
            )
            for row in priority_rows
        ],
        key=lambda x: priority_order.get(x.priority, 4),
    )


def _get_average_coverage_score(
    assessment_id: uuid.UUID, session: Session
) -> float | None:
    """
    Compute Average Coverage Score for completed activities.
    """
    result = session.execute(
        select(func.avg(ActivityEvaluation.activity_coverage_score))
        .select_from(Activity)
        .join(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            *_VISIBILITY_FILTERS,
        )
    ).scalar()

    return float(result) if result is not None else None


def _get_average_coverage_scores_by_priority(
    assessment_id: uuid.UUID, session: Session
) -> list[PriorityAverageScoreItem]:
    """
    Compute Average Coverage Score per Priority for completed activities.
    """
    results = session.execute(
        select(Activity.priority, func.avg(ActivityEvaluation.activity_coverage_score))
        .select_from(Activity)
        .join(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            Activity.priority.is_not(None),
            *_VISIBILITY_FILTERS,
        )
        .group_by(Activity.priority)
    ).all()

    # Create a mapping of the DB results
    score_map = {
        priority: float(avg_score) if avg_score is not None else None
        for priority, avg_score in results
    }

    # Return all 4 priorities explicitly to ensure they always exist in the response
    return [
        PriorityAverageScoreItem(
            priority=priority.value, average_score=score_map.get(priority.value)
        )
        for priority in ActivityPriority
        # Handle the case where ActivityPriority enum might contain None/Unknown if defined, but based on typical setup we iterate the enum
    ]


def _get_mitre_tactic_scores(
    assessment_id: uuid.UUID, session: Session
) -> list[MitreTacticScoreItem]:
    """
    Compute performance scores clustered by MITRE Tactic and Technique.
    """

    # We only care about activities that have both a tactic and technique assigned.
    # To compute a percentage, we use avg() on a case statement mapping True to 100.0 and False to 0.0.
    # The else_=None ensures we only average rows where expected was True.
    # e.g. If expected_logging=True and logged=True -> 100.0
    def _calc_expected_percent(expected_col):
        return func.avg(case((expected_col.is_(True), 100.0), else_=0.0))

    def _calc_actual_percent(expected_col, actual_col):
        return func.avg(
            case((and_(expected_col.is_(True), actual_col.is_(True)), 100.0), else_=0.0)
        )

    results = session.execute(
        select(
            Activity.mitre_tactic,
            Tactic.name.label("tactic_name"),
            Activity.mitre_technique,
            Technique.name.label("technique_name"),
            func.avg(ActivityEvaluation.activity_coverage_score).label("overall_score"),
            _calc_expected_percent(Activity.expected_logging).label(
                "expected_logged_score"
            ),
            _calc_actual_percent(Activity.expected_logging, Activity.logged).label(
                "logged_score"
            ),
            _calc_expected_percent(Activity.expected_prevention).label(
                "expected_prevented_score"
            ),
            _calc_actual_percent(
                Activity.expected_prevention, Activity.prevented
            ).label("prevented_score"),
            _calc_expected_percent(Activity.expected_alert_creation).label(
                "expected_alerted_score"
            ),
            _calc_actual_percent(
                Activity.expected_alert_creation, Activity.alerted
            ).label("alerted_score"),
            _calc_expected_percent(Activity.expected_stakeholder_notification).label(
                "expected_notified_score"
            ),
            _calc_actual_percent(
                Activity.expected_stakeholder_notification,
                Activity.stakeholder_notification_created,
            ).label("stakeholder_notified_score"),
        )
        .select_from(Activity)
        .join(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .outerjoin(Tactic, Activity.mitre_tactic == Tactic.mitre_id)
        .outerjoin(Technique, Activity.mitre_technique == Technique.mitre_id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            Activity.mitre_tactic.is_not(None),
            Activity.mitre_technique.is_not(None),
            *_VISIBILITY_FILTERS,
        )
        .group_by(
            Activity.mitre_tactic, Tactic.name, Activity.mitre_technique, Technique.name
        )
    ).all()

    # Group the techniques by tactic in Python
    tactics_map: dict[str, list[MitreTechniqueScoreItem]] = {}

    for row in results:
        (
            tactic_id,
            tactic_name,
            technique_id,
            technique_name,
            overall,
            exp_logged,
            logged,
            exp_prevented,
            prevented,
            exp_alerted,
            alerted,
            exp_notified,
            notified,
        ) = row

        if not tactic_id or not technique_id:
            continue

        tactic_display = f"{tactic_name} - {tactic_id}" if tactic_name else tactic_id
        technique_display = (
            f"{technique_name} - {technique_id}" if technique_name else technique_id
        )

        technique_item = MitreTechniqueScoreItem(
            technique=technique_display,
            overall_score=float(overall) if overall is not None else None,
            expected_logged_score=float(exp_logged) if exp_logged is not None else None,
            logged_score=float(logged) if logged is not None else None,
            expected_prevented_score=float(exp_prevented)
            if exp_prevented is not None
            else None,
            prevented_score=float(prevented) if prevented is not None else None,
            expected_alerted_score=float(exp_alerted)
            if exp_alerted is not None
            else None,
            alerted_score=float(alerted) if alerted is not None else None,
            expected_stakeholder_notified_score=float(exp_notified)
            if exp_notified is not None
            else None,
            stakeholder_notified_score=float(notified)
            if notified is not None
            else None,
        )

        if tactic_display not in tactics_map:
            tactics_map[tactic_display] = []
        tactics_map[tactic_display].append(technique_item)

    return [
        MitreTacticScoreItem(tactic=tactic, techniques=techniques)
        for tactic, techniques in tactics_map.items()
    ]


def _get_mitre_overall_tactic_scores(
    assessment_id: uuid.UUID, session: Session
) -> list[MitreOverallTacticScoreItem]:
    """Compute performance scores clustered by MITRE Tactic overall."""

    def _calc_expected_percent(expected_col):
        return func.avg(case((expected_col.is_(True), 100.0), else_=0.0))

    def _calc_actual_percent(expected_col, actual_col):
        return func.avg(
            case((and_(expected_col.is_(True), actual_col.is_(True)), 100.0), else_=0.0)
        )

    results = session.execute(
        select(
            Activity.mitre_tactic,
            Tactic.name.label("tactic_name"),
            func.avg(ActivityEvaluation.activity_coverage_score).label("overall_score"),
            _calc_expected_percent(Activity.expected_logging).label(
                "expected_logged_score"
            ),
            _calc_actual_percent(Activity.expected_logging, Activity.logged).label(
                "logged_score"
            ),
            _calc_expected_percent(Activity.expected_prevention).label(
                "expected_prevented_score"
            ),
            _calc_actual_percent(
                Activity.expected_prevention, Activity.prevented
            ).label("prevented_score"),
            _calc_expected_percent(Activity.expected_alert_creation).label(
                "expected_alerted_score"
            ),
            _calc_actual_percent(
                Activity.expected_alert_creation, Activity.alerted
            ).label("alerted_score"),
            _calc_expected_percent(Activity.expected_stakeholder_notification).label(
                "expected_notified_score"
            ),
            _calc_actual_percent(
                Activity.expected_stakeholder_notification,
                Activity.stakeholder_notification_created,
            ).label("stakeholder_notified_score"),
        )
        .select_from(Activity)
        .join(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .outerjoin(Tactic, Activity.mitre_tactic == Tactic.mitre_id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            Activity.mitre_tactic.is_not(None),
            *_VISIBILITY_FILTERS,
        )
        .group_by(Activity.mitre_tactic, Tactic.name)
    ).all()

    items = []
    for row in results:
        (
            tactic_id,
            tactic_name,
            overall,
            exp_logged,
            logged,
            exp_prevented,
            prevented,
            exp_alerted,
            alerted,
            exp_notified,
            notified,
        ) = row

        if not tactic_id:
            continue

        tactic_display = f"{tactic_name} - {tactic_id}" if tactic_name else tactic_id

        items.append(
            MitreOverallTacticScoreItem(
                tactic=tactic_display,
                overall_score=float(overall) if overall is not None else None,
                expected_logged_score=float(exp_logged)
                if exp_logged is not None
                else None,
                logged_score=float(logged) if logged is not None else None,
                expected_prevented_score=float(exp_prevented)
                if exp_prevented is not None
                else None,
                prevented_score=float(prevented) if prevented is not None else None,
                expected_alerted_score=float(exp_alerted)
                if exp_alerted is not None
                else None,
                alerted_score=float(alerted) if alerted is not None else None,
                expected_stakeholder_notified_score=float(exp_notified)
                if exp_notified is not None
                else None,
                stakeholder_notified_score=float(notified)
                if notified is not None
                else None,
            )
        )

    return items


def _get_mean_time_metrics(
    assessment_id: uuid.UUID, session: Session
) -> list[MeanTimeMetricsItem]:
    """
    Compute mean time to detect and respond grouped by priority.
    """
    results = session.execute(
        select(
            Activity.priority,
            func.avg(
                func.extract(
                    "epoch", Activity.alert_time - Activity.activity_start_time
                )
            ).label("mttd"),
            func.avg(
                func.extract(
                    "epoch",
                    Activity.stakeholder_notification_time - Activity.alert_time,
                )
            ).label("mttr"),
        )
        .select_from(Activity)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            Activity.priority.is_not(None),
            *_VISIBILITY_FILTERS,
        )
        .group_by(Activity.priority)
    ).all()

    items = []
    for row in results:
        items.append(
            MeanTimeMetricsItem(
                priority=row.priority.value
                if hasattr(row.priority, "value")
                else row.priority,
                mean_time_to_detect_seconds=float(row.mttd)
                if row.mttd is not None
                else None,
                mean_time_to_respond_seconds=float(row.mttr)
                if row.mttr is not None
                else None,
            )
        )
    return items


def _get_severity_accuracy(
    assessment_id: uuid.UUID, session: Session
) -> list[SeverityAccuracyItem]:
    """
    Compute the accuracy between expected severity and actual generated alert severity.
    """
    results = session.execute(
        select(
            Activity.expected_severity,
            func.coalesce(
                func.sum(
                    case((Activity.alert_severity.ilike("%informational%"), 1), else_=0)
                ),
                0,
            ).label("actual_informational"),
            func.coalesce(
                func.sum(case((Activity.alert_severity.ilike("%low%"), 1), else_=0)), 0
            ).label("actual_low"),
            func.coalesce(
                func.sum(case((Activity.alert_severity.ilike("%medium%"), 1), else_=0)),
                0,
            ).label("actual_medium"),
            func.coalesce(
                func.sum(case((Activity.alert_severity.ilike("%high%"), 1), else_=0)), 0
            ).label("actual_high"),
            func.coalesce(
                func.sum(
                    case((Activity.alert_severity.ilike("%critical%"), 1), else_=0)
                ),
                0,
            ).label("actual_critical"),
            func.coalesce(
                func.sum(
                    case(
                        (Activity.alert_severity.is_(None), 1),
                        (
                            and_(
                                Activity.alert_severity.not_ilike("%informational%"),
                                Activity.alert_severity.not_ilike("%low%"),
                                Activity.alert_severity.not_ilike("%medium%"),
                                Activity.alert_severity.not_ilike("%high%"),
                                Activity.alert_severity.not_ilike("%critical%"),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("actual_none"),
        )
        .select_from(Activity)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .where(
            Activity.assessment_id == assessment_id,
            Activity.state == ActivityState.COMPLETED,
            Activity.expected_severity.is_not(None),
            *_VISIBILITY_FILTERS,
        )
        .group_by(Activity.expected_severity)
    ).all()

    items = []
    for row in results:
        items.append(
            SeverityAccuracyItem(
                expected_severity=row.expected_severity.value
                if hasattr(row.expected_severity, "value")
                else row.expected_severity,
                actual_informational=int(row.actual_informational),
                actual_low=int(row.actual_low),
                actual_medium=int(row.actual_medium),
                actual_high=int(row.actual_high),
                actual_critical=int(row.actual_critical),
                actual_none=int(row.actual_none),
            )
        )
    return items


def get_assessment_statistics_service(
    assessment_id: uuid.UUID,
    session: Session,
) -> AssessmentStatisticsResponse:
    """
    Compute assessment statistics over visible, non-deleted activities
    in visible, non-deleted groups. All roles see the same data.
    """
    return AssessmentStatisticsResponse(
        state_distribution=_get_state_distribution(assessment_id, session),
        priority_breakdown=_get_priority_breakdown(assessment_id, session),
        average_coverage_score=_get_average_coverage_score(assessment_id, session),
        average_coverage_scores_by_priority=_get_average_coverage_scores_by_priority(
            assessment_id, session
        ),
        mitre_overall_tactic_scores=_get_mitre_overall_tactic_scores(
            assessment_id, session
        ),
        mitre_tactic_scores=_get_mitre_tactic_scores(assessment_id, session),
        mean_time_metrics=_get_mean_time_metrics(assessment_id, session),
        severity_accuracy=_get_severity_accuracy(assessment_id, session),
    )
