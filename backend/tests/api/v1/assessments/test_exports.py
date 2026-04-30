import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums.enums import ActivityState
from app.models.activity import Activity
from app.models.activity_evaluation import ActivityEvaluation
from app.models.assessment import Assessment
from app.models.mitre import Tactic, Technique
from app.models.user import User


@pytest.fixture
def test_assessment_fixture(session: Session, test_admin_user: User) -> Assessment:
    assessment = Assessment(
        name="Test Assessment",
        description="A test assessment",
        assessment_type="RedTeam",
        created_by=test_admin_user.id,
    )
    session.add(assessment)
    session.commit()
    return assessment


@pytest.fixture
def test_acl_red_fixture(
    session: Session, test_regular_user: User, test_assessment_fixture: Assessment
) -> None:
    from app.models.acl import Acl

    acl = Acl(
        user_id=test_regular_user.id,
        assessment_id=test_assessment_fixture.id,
        assessment_role="red",
        created_by=test_regular_user.id,
    )
    session.add(acl)
    session.commit()


@pytest.fixture
def test_mitre_data_fixture(session: Session) -> dict:
    t1 = Tactic(mitre_id="TA0001", name="Initial Access")
    t2 = Tactic(mitre_id="TA0002", name="Execution")
    tech1 = Technique(mitre_id="T1190", name="Exploit Public-Facing Application")
    tech2 = Technique(mitre_id="T1059", name="Command and Scripting Interpreter")

    tech1.tactics = [t1]
    tech2.tactics = [t2]

    session.add_all([t1, t2, tech1, tech2])
    session.commit()

    return {"t1": t1, "t2": t2, "tech1": tech1, "tech2": tech2}


@pytest.fixture
def test_scored_activity_fixture(
    session: Session,
    test_assessment_fixture: Assessment,
    test_regular_user: User,
    test_mitre_data_fixture: dict,
) -> Activity:
    activity_1 = Activity(
        name="Successful Exploit",
        assessment_id=test_assessment_fixture.id,
        created_by=test_regular_user.id,
        state=ActivityState.COMPLETED,
        mitre_tactic=test_mitre_data_fixture["t1"].mitre_id,
        mitre_technique=test_mitre_data_fixture["tech1"].mitre_id,
    )
    session.add(activity_1)
    session.commit()

    eval_1 = ActivityEvaluation(
        activity_id=activity_1.id,
        activity_coverage_score=80.0,
    )
    session.add(eval_1)
    session.commit()

    return activity_1


def test_generate_mitre_attack_navigator_layer(
    client: TestClient,
    auth_headers_regular: dict[str, str],
    test_assessment_fixture: Assessment,
    test_acl_red_fixture: None,
    test_scored_activity_fixture: Activity,
):
    """
    Test generating the MITRE ATT&CK Navigator Layer
    """
    response = client.post(
        f"/api/v1/assessments/{test_assessment_fixture.id}/export/mitre",
        headers=auth_headers_regular,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert (
        'attachment; filename="mitre_attack_navigator_export.json"'
        in response.headers["content-disposition"]
    )

    data = response.json()
    assert data["name"] == "Test Assessment Reporting"
    assert "techniques" in data

    # We should have two techniques mapped from the mock database
    techs = data["techniques"]
    assert len(techs) == 2

    # One is scored, one is not
    scored_tech = next((t for t in techs if t["techniqueID"] == "T1190"), None)
    unscored_tech = next((t for t in techs if t["techniqueID"] == "T1059"), None)

    assert scored_tech is not None
    assert scored_tech["score"] == 80
    assert scored_tech["enabled"] is True
    assert scored_tech["tactic"] == "initial-access"

    assert unscored_tech is not None
    assert unscored_tech["enabled"] is False
    assert "score" not in unscored_tech
