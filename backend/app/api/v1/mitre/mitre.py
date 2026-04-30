from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.mitre import (
    MitreFilter,
    TacticBase,
    TacticWithTechniques,
    TechniqueBase,
    TechniqueWithTactics,
)
from app.services.mitre.mitre import (
    get_all_tactics_service,
    get_all_techniques_service,
    get_tactics_with_techniques_service,
    get_techniques_with_tactics_service,
)

router = APIRouter(
    prefix="/mitre",
    tags=["mitre"],
)


@router.get("/tactics", response_model=list[TacticBase])
def read_tactics(
    filter_query: Annotated[MitreFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all tactics
    """
    tactics = get_all_tactics_service(user, session, filter_query)
    return tactics


@router.get("/tactics-with-techniques", response_model=list[TacticWithTechniques])
def read_tactics_with_techniques(
    filter_query: Annotated[MitreFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get tactics with its associated techniques.
    """
    tactics = get_tactics_with_techniques_service(user, session, filter_query)
    return tactics


@router.get("/techniques", response_model=list[TechniqueBase])
def read_techniques(
    filter_query: Annotated[MitreFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get all techniques
    """
    techniques = get_all_techniques_service(user, session, filter_query)
    return techniques


@router.get("/techniques-with-tactics", response_model=list[TechniqueWithTactics])
def read_techniques_with_tactics(
    filter_query: Annotated[MitreFilter, Query()],
    user: User = Depends(mfa_validation_service),
    session: Session = Depends(get_session),
):
    """
    Get techniques with its associated tactics.
    """
    techniques = get_techniques_with_tactics_service(user, session, filter_query)
    return techniques
