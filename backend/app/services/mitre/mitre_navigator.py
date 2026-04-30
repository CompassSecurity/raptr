import json
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.enums.enums import ActivityState
from app.models.activity import Activity
from app.models.activity_evaluation import ActivityEvaluation
from app.models.mitre import Tactic, Technique
from app.models.user import User
from app.schemas.report import GeneratedReport
from app.services.assessment.assessment import get_assessment_by_id_service


def generate_mitre_navigator_layer_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> GeneratedReport:
    """
    Generate a MITRE ATT&CK Navigator layer for the assessment.
    Returns a file download (JSON).
    """
    assessment = get_assessment_by_id_service(assessment_id, user, session)
    assessment_name = assessment.name

    results = (
        session.query(
            Tactic.name,
            Activity.mitre_technique,
            func.avg(ActivityEvaluation.activity_coverage_score).label("average_score"),
        )
        .join(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
        .outerjoin(Tactic, Activity.mitre_tactic == Tactic.mitre_id)
        .filter(
            Activity.assessment_id == assessment_id,
            Activity.deleted.is_(False),
            Activity.state == ActivityState.COMPLETED,
        )
        .group_by(Tactic.name, Activity.mitre_technique)
        .all()
    )

    scored_map = {}
    for tactic_name, technique, avg_score in results:
        formatted_tactic = tactic_name.lower().replace(" ", "-") if tactic_name else ""
        scored_map[(formatted_tactic, technique)] = (
            round(float(avg_score)) if avg_score is not None else 0
        )

    all_techniques = (
        session.query(Technique).options(selectinload(Technique.tactics)).all()
    )

    techniques = []
    for tech in all_techniques:
        for tac in tech.tactics:
            formatted_tactic = tac.name.lower().replace(" ", "-") if tac.name else ""
            key = (formatted_tactic, tech.mitre_id)
            if key in scored_map:
                techniques.append(
                    {
                        "techniqueID": tech.mitre_id,
                        "tactic": formatted_tactic,
                        "score": scored_map[key],
                        "enabled": True,
                    }
                )
            else:
                techniques.append(
                    {
                        "techniqueID": tech.mitre_id,
                        "tactic": formatted_tactic,
                        "color": "",
                        "comment": "",
                        "enabled": False,
                        "metadata": [],
                        "links": [],
                        "showSubtechniques": True,
                    }
                )

    # Some activities might have techniques not found in the DB
    known_keys = set(
        (tac.name.lower().replace(" ", "-") if tac.name else "", tech.mitre_id)
        for tech in all_techniques
        for tac in tech.tactics
    )
    for (formatted_tactic, technique), score in scored_map.items():
        if (formatted_tactic, technique) not in known_keys:
            techniques.append(
                {
                    "techniqueID": technique,
                    "tactic": formatted_tactic,
                    "score": score,
                    "enabled": True,
                }
            )

    layer_data = {
        "name": f"{assessment_name} Reporting",
        "versions": {"layer": "4.5"},
        "domain": "enterprise-attack",
        "sorting": 3,
        "layout": {
            "layout": "flat",
            "aggregateFunction": "average",
            "showID": True,
            "showName": True,
            "showAggregateScores": True,
            "countUnscored": False,
        },
        "hideDisabled": True,
        "techniques": techniques,
        "gradient": {
            "colors": ["#ff6666ff", "#ffe766ff", "#8ec843ff"],
            "minValue": 0,
            "maxValue": 100,
        },
        "showTacticRowBackground": True,
        "tacticRowBackground": "#593196",
        "selectTechniquesAcrossTactics": False,
        "selectSubtechniquesWithParent": False,
    }

    json_content = json.dumps(layer_data, indent=4).encode("utf-8")

    return GeneratedReport(
        content=json_content,
        media_type="application/json",
        filename="mitre_attack_navigator_export.json",
    )
