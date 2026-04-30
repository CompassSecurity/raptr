from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.mitre import Tactic, Technique
from app.models.user import User
from app.schemas.mitre import MitreFilter
from app.services.utils.query import query


def get_all_tactics_service(
    user: User,
    session: Session,
    filter_query: MitreFilter,
) -> list[Tactic]:
    """
    Get all tactics
    """
    statement = select(Tactic)
    return query(session, Tactic, filter_query, statement)


def get_all_techniques_service(
    user: User,
    session: Session,
    filter_query: MitreFilter,
) -> list[Technique]:
    """
    Get all techniques
    """
    statement = select(Technique)
    return query(session, Technique, filter_query, statement)


def get_tactics_with_techniques_service(
    user: User,
    session: Session,
    filter_query: MitreFilter,
) -> list[Tactic]:
    """
    Get tactics with its associated techniques
    """
    statement = select(Tactic).options(selectinload(Tactic.techniques))
    tactics = query(session, Tactic, filter_query, statement)

    if filter_query.sort_by:
        is_descending = filter_query.sort_order == "desc"
        sort_field = filter_query.sort_by

        for tactic in tactics:

            def get_sort_key(technique):
                value = getattr(technique, sort_field)
                return value if value is not None else ""

            tactic.techniques.sort(key=get_sort_key, reverse=is_descending)

    return tactics


def get_techniques_with_tactics_service(
    user: User,
    session: Session,
    filter_query: MitreFilter,
) -> list[Technique]:
    """
    Get techniques with its associated tactics
    """
    statement = select(Technique).options(selectinload(Technique.tactics))
    techniques = query(session, Technique, filter_query, statement)

    if filter_query.sort_by:
        sort_field = filter_query.sort_by
        is_descending = filter_query.sort_order == "desc"

        for technique in techniques:

            def tactic_sort_key(tactic):
                value = getattr(tactic, sort_field)
                return value if value is not None else ""

            technique.tactics.sort(key=tactic_sort_key, reverse=is_descending)

    return techniques
