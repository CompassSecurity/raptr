import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.orm import Session

from app.models.mitre import Tactic, Technique
from app.schemas.mitre import MitreFilter
from app.services.mitre.mitre import (
    get_all_tactics_service,
    get_all_techniques_service,
    get_tactics_with_techniques_service,
    get_techniques_with_tactics_service,
)
from app.services.seed.mitre import (
    download_mitre_data,
    parse_and_ingest_mitre_data_service,
)

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


def test_download_mitre_data():
    async def run_test():
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = SAMPLE_MITRE_DATA
            mock_response.raise_for_status.return_value = None

            mock_get.return_value = mock_response

            data = await download_mitre_data()
            assert data == SAMPLE_MITRE_DATA
            mock_get.assert_called_once()

    asyncio.run(run_test())


def test_parse_and_ingest_mitre_data_service(session: Session):
    # Test Ingestion
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)

    # Verify Tactic
    tactic = session.query(Tactic).filter_by(mitre_id="TA0001").first()
    assert tactic is not None
    assert tactic.name == "Initial Access"

    # Verify Technique
    technique = session.query(Technique).filter_by(mitre_id="T1566").first()
    assert technique is not None
    assert technique.name == "Phishing"

    # Verify Relationship
    assert len(technique.tactics) == 1
    assert technique.tactics[0].mitre_id == "TA0001"


def test_parse_and_ingest_mitre_data_service_idempotency(session: Session):
    # Run twice
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)

    # Check counts should verify no duplicates
    assert session.query(Tactic).count() == 1
    assert session.query(Technique).count() == 1


def test_get_services(session: Session, test_admin_user):
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)

    # Test get_all_tactics_service
    tactics = get_all_tactics_service(test_admin_user, session, MitreFilter())
    assert len(tactics) == 1
    assert tactics[0].mitre_id == "TA0001"

    # Test get_all_techniques_service
    techniques = get_all_techniques_service(test_admin_user, session, MitreFilter())
    assert len(techniques) == 1
    assert techniques[0].mitre_id == "T1566"

    # Test get_tactics_with_techniques_service
    tactics_w_tech = get_tactics_with_techniques_service(
        test_admin_user, session, MitreFilter()
    )
    assert len(tactics_w_tech) == 1
    assert len(tactics_w_tech[0].techniques) == 1
    assert tactics_w_tech[0].techniques[0].mitre_id == "T1566"

    # Test get_techniques_with_tactics_service
    tech_w_tactics = get_techniques_with_tactics_service(
        test_admin_user, session, MitreFilter()
    )
    assert len(tech_w_tactics) == 1
    assert len(tech_w_tactics[0].tactics) == 1
    assert tech_w_tactics[0].tactics[0].mitre_id == "TA0001"


def test_search_functionality(session: Session, test_admin_user):
    parse_and_ingest_mitre_data_service(session, SAMPLE_MITRE_DATA)

    # Search by name
    tactics = get_all_tactics_service(
        test_admin_user, session, MitreFilter(name="Initial")
    )
    assert len(tactics) == 1

    # Search by mitre_id
    techniques = get_all_techniques_service(
        test_admin_user, session, MitreFilter(mitre_id="T1566")
    )
    assert len(techniques) == 1

    # Search no match
    tactics = get_all_tactics_service(
        test_admin_user, session, MitreFilter(name="NonExistent")
    )
    assert len(tactics) == 0
