from sqlalchemy import select
from sqlalchemy.orm import Session


def health_check_service(session: Session) -> str:
    """
    Check the health of the server and database.
    """
    try:
        session.execute(select(1))
        return "Server and database are online"
    except Exception:
        return "Server is online, but database connection failed"
