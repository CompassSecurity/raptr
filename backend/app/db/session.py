from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger

app_logger.debug("Database Engine: %s", settings.DB_ENGINE)

if settings.DB_ENGINE == "sqlite":
    app_logger.debug("Database Path: %s", settings.SQLITE_DB_PATH)
else:
    app_logger.debug("Database Host: %s", settings.POSTGRES_HOST)
    app_logger.debug("Database Port: %s", settings.POSTGRES_PORT)
    app_logger.debug("Database User: %s", settings.POSTGRES_USER)
    app_logger.debug("Database Name: %s", settings.POSTGRES_DB)


if settings.DB_ENGINE == "sqlite":
    DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"
else:
    DATABASE_URL = f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DB_ENGINE == "sqlite" and "sqlite3" in str(type(dbapi_connection)):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI Dependency: Provides a database session.
    """
    with Session(engine) as session:
        yield session
