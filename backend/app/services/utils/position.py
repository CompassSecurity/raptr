from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement


def calculate_new_position(
    session: Session,
    model_column: InstrumentedAttribute,
    filters: list[ColumnElement],
) -> int:
    """
    Calculate the next available position for a given model column and filters.
    Returns max_position + 1, or 0 if no records exist.
    """
    statement = select(func.max(model_column)).where(*filters)
    max_pos = session.execute(statement).scalar()
    return (max_pos + 1) if max_pos is not None else 0


def calculate_new_activity_position(
    session: Session,
    group_id: uuid.UUID,
) -> int:
    """
    Calculate the next activity_position for an activity in a group.
    Returns max+1 or 0 for empty groups.
    """
    from app.models.activity import Activity

    return calculate_new_position(
        session,
        Activity.activity_position,
        [Activity.activity_group_id == group_id],
    )
