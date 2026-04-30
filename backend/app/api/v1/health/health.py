from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.general import MessageResponse
from app.services.health.health import health_check_service

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/")
def health_check(
    session: Session = Depends(get_session),
) -> MessageResponse:
    """
    Check the health of the server and database.
    """
    msg = health_check_service(session)
    return MessageResponse(message=msg)
