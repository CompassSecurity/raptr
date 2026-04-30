import httpx
from fastapi import HTTPException, status
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.models.mitre import Tactic, Technique
from app.services.utils.memory import release_memory


def _get_insert_func(session: Session):
    dialect = session.bind.dialect.name
    if dialect == "sqlite":
        return sqlite.insert
    return postgresql.insert


async def download_mitre_data() -> dict:
    """
    Downloads the MITRE ATT&CK Enterprise JSON.
    """
    async with httpx.AsyncClient() as client:
        try:
            app_logger.debug("Downloading MITRE ATT&CK data...")
            response = await client.get(settings.MITRE_JSON_URL)
            response.raise_for_status()
            app_logger.info("MITRE ATT&CK data downloaded successfully")
            return response.json()
        except httpx.HTTPError as e:
            app_logger.error(f"Failed to download MITRE data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download MITRE data",
            )


def parse_and_ingest_mitre_data_service(
    session: Session,
    data: dict,
) -> None:
    """
    Parses MITRE ATT&CK JSON and ingests Tactics and Techniques into the database.
    """
    # 1. Parse Tactics
    tactics_map = {}  # mitre_id -> Tactic object (for relationship linking)

    # First pass: Create/Update Tactics
    for obj in data.get("objects", []):
        if obj.get("type") == "x-mitre-tactic":
            # Skip deprecated or revoked tactics
            if obj.get("x_mitre_deprecated", False) or obj.get("revoked", False):
                continue
            external_refs = obj.get("external_references", [])
            mitre_ref = next(
                (
                    ref
                    for ref in external_refs
                    if ref.get("source_name") == "mitre-attack"
                ),
                None,
            )
            mitre_id = mitre_ref.get("external_id") if mitre_ref else None

            if not mitre_id:
                continue

            insert_func = _get_insert_func(session)
            stmt = (
                insert_func(Tactic)
                .values(
                    mitre_id=mitre_id,
                    name=obj.get("name", ""),
                    url=mitre_ref.get("url"),
                )
                .on_conflict_do_update(
                    index_elements=["mitre_id"],
                    set_=dict(name=obj.get("name", ""), url=mitre_ref.get("url")),
                )
                .returning(Tactic)
            )

            result = session.execute(stmt)
            tactic = result.scalar_one()
            tactics_map[obj.get("x_mitre_shortname")] = tactic

    session.commit()

    # 2. Parse Techniques and Link to Tactics
    for obj in data.get("objects", []):
        if obj.get("type") == "attack-pattern":
            # Skip deprecated or revoked techniques
            if obj.get("x_mitre_deprecated", False) or obj.get("revoked", False):
                continue
            external_refs = obj.get("external_references", [])
            mitre_ref = next(
                (
                    ref
                    for ref in external_refs
                    if ref.get("source_name") == "mitre-attack"
                ),
                None,
            )
            mitre_id = mitre_ref.get("external_id") if mitre_ref else None

            if not mitre_id:
                continue

            # Insert/Update Technique
            insert_func = _get_insert_func(session)
            stmt = (
                insert_func(Technique)
                .values(
                    mitre_id=mitre_id,
                    name=obj.get("name", ""),
                    url=mitre_ref.get("url"),
                )
                .on_conflict_do_update(
                    index_elements=["mitre_id"],
                    set_=dict(name=obj.get("name", ""), url=mitre_ref.get("url")),
                )
                .returning(Technique)
            )

            result = session.execute(stmt)
            technique = result.scalar_one()

            # Link Tactics
            kill_chain_phases = obj.get("kill_chain_phases", [])
            current_tactics = []
            for phase in kill_chain_phases:
                if phase.get("kill_chain_name") == "mitre-attack":
                    phase_name = phase.get("phase_name")
                    if phase_name in tactics_map:
                        current_tactics.append(tactics_map[phase_name])

            # Update relationship (this might need optimization for bulk but works for this scale)
            technique.tactics = current_tactics
            session.add(technique)

    session.commit()
    release_memory()
