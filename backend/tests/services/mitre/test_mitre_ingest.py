import pytest
from sqlalchemy import select

from app.models.mitre import Tactic, Technique
from app.services.seed.mitre import parse_and_ingest_mitre_data_service


@pytest.fixture
def sample_mitre_data():
    return {
        "objects": [
            {
                "type": "x-mitre-tactic",
                "name": "Initial Access",
                "x_mitre_shortname": "initial-access",
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": "TA0001",
                        "url": "https://attack.mitre.org/tactics/TA0001",
                    }
                ],
            },
            {
                "type": "x-mitre-tactic",
                "name": "Execution",
                "x_mitre_shortname": "execution",
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": "TA0002",
                        "url": "https://attack.mitre.org/tactics/TA0002",
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
            {
                "type": "attack-pattern",
                "name": "Command and Scripting Interpreter",
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": "T1059",
                        "url": "https://attack.mitre.org/techniques/T1059",
                    }
                ],
                "kill_chain_phases": [
                    {"kill_chain_name": "mitre-attack", "phase_name": "execution"}
                ],
            },
        ]
    }


def test_parse_and_ingest_mitre_data_service(session, sample_mitre_data):
    parse_and_ingest_mitre_data_service(session, sample_mitre_data)

    # Check tactics were created
    tactics = session.execute(select(Tactic)).scalars().all()
    assert len(tactics) >= 2

    tactic_names = [t.name for t in tactics]
    assert "Initial Access" in tactic_names
    assert "Execution" in tactic_names

    # Check techniques were created
    techniques = session.execute(select(Technique)).scalars().all()
    assert len(techniques) >= 2

    technique_names = [t.name for t in techniques]
    assert "Phishing" in technique_names
    assert "Command and Scripting Interpreter" in technique_names


def test_parse_and_ingest_mitre_data_service_links_tactics(session, sample_mitre_data):
    parse_and_ingest_mitre_data_service(session, sample_mitre_data)

    # Get technique and check it's linked to tactic
    phishing = session.execute(
        select(Technique).where(Technique.mitre_id == "T1566")
    ).scalar_one()

    assert len(phishing.tactics) == 1
    assert phishing.tactics[0].mitre_id == "TA0001"


def test_parse_and_ingest_mitre_data_service_upsert(session, sample_mitre_data):
    # First ingest
    parse_and_ingest_mitre_data_service(session, sample_mitre_data)

    tactics_count_1 = len(session.execute(select(Tactic)).scalars().all())

    # Second ingest (should not duplicate)
    parse_and_ingest_mitre_data_service(session, sample_mitre_data)

    tactics_count_2 = len(session.execute(select(Tactic)).scalars().all())

    assert tactics_count_1 == tactics_count_2
