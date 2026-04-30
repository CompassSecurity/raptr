from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.seed.mitre import parse_and_ingest_mitre_data_service

SAMPLE_MITRE_DATA = {
    "objects": [
        {
            "type": "x-mitre-tactic",
            "x_mitre_shortname": "initial-access",
            "name": "Initial Access",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "external_id": "TA0001",
                    "url": "https://attack.mitre.org/tactics/TA0001",
                }
            ],
        },
        {
            "type": "attack-pattern",
            "name": "Phishing",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "external_id": "T1566",
                    "url": "https://attack.mitre.org/techniques/T1566",
                }
            ],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "initial-access"}
            ],
        },
    ]
}


def setup_mitre_data(session: Session):
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)


def test_read_tactics(
    client: TestClient, session: Session, auth_headers_regular: dict[str, str]
):
    setup_mitre_data(session)
    response = client.get("/api/v1/mitre/tactics", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mitre_id"] == "TA0001"


def test_read_tactics_unauthenticated(client: TestClient, session: Session):
    response = client.get("/api/v1/mitre/tactics")
    assert response.status_code == 401


def test_read_techniques(
    client: TestClient, session: Session, auth_headers_regular: dict[str, str]
):
    setup_mitre_data(session)
    response = client.get("/api/v1/mitre/techniques", headers=auth_headers_regular)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mitre_id"] == "T1566"


def test_read_techniques_unauthenticated(client: TestClient, session: Session):
    response = client.get("/api/v1/mitre/techniques")
    assert response.status_code == 401


def test_read_tactics_with_techniques(
    client: TestClient, session: Session, auth_headers_regular: dict[str, str]
):
    setup_mitre_data(session)
    response = client.get(
        "/api/v1/mitre/tactics-with-techniques", headers=auth_headers_regular
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mitre_id"] == "TA0001"
    assert len(data[0]["techniques"]) == 1
    assert data[0]["techniques"][0]["mitre_id"] == "T1566"


def test_read_techniques_with_tactics(
    client: TestClient, session: Session, auth_headers_regular: dict[str, str]
):
    setup_mitre_data(session)
    response = client.get(
        "/api/v1/mitre/techniques-with-tactics", headers=auth_headers_regular
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mitre_id"] == "T1566"
    assert len(data[0]["tactics"]) == 1
    assert data[0]["tactics"][0]["mitre_id"] == "TA0001"
