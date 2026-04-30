import secrets
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.core.password import generate_secure_password
from app.db.session import engine
from app.enums.enums import UserRole
from app.models.base import Base
from app.schemas.user import UserCreate
from app.services.user.user import check_user_exists_service, create_user_service


def ensure_secret_key() -> None:
    """
    Ensure SECRET_KEY exists in .env file. Generate and save if missing.
    """
    from app.core.config import settings

    if not settings.SECRET_KEY:
        app_logger.warning(
            "SECRET_KEY not found in .env file. Generating a new secure key..."
        )

        # Generate a secure random 64-character hex string
        new_secret_key = secrets.token_hex(32)

        # Path to .env file
        env_file = Path(".env")

        # Append SECRET_KEY to .env file
        with open(env_file, "a") as f:
            f.write(
                f'\n# Auto-generated SECRET_KEY for JWT tokens\nSECRET_KEY="{new_secret_key}"\n'
            )

        app_logger.info("SECRET_KEY generated and saved to .env file")

        # Update the settings object with the new key
        settings.SECRET_KEY = new_secret_key
    else:
        app_logger.debug("SECRET_KEY loaded from .env file")


def ensure_admin_password() -> None:
    """
    Ensure ADMIN_PASSWORD exists in .env file. Generate and save if missing.
    """
    if not settings.ADMIN_PASSWORD:
        app_logger.warning(
            "ADMIN_PASSWORD not found in .env file. Generating a new secure password..."
        )

        # Generate a secure random URL-safe string
        new_admin_password = generate_secure_password(32)

        # Path to .env file
        env_file = Path(".env")

        # Append ADMIN_PASSWORD to .env file
        with open(env_file, "a") as f:
            f.write(
                f'\n# Auto-generated ADMIN_PASSWORD for admin user\nADMIN_PASSWORD="{new_admin_password}"\n'
            )

        app_logger.info("ADMIN_PASSWORD generated and saved to .env file")

        # Update the settings object with the new password
        settings.ADMIN_PASSWORD = new_admin_password
    else:
        app_logger.debug("ADMIN_PASSWORD loaded from .env file")


def create_db_and_tables() -> None:
    """
    Called once at application startup to create all database tables
    defined by SQLAlchemy models.
    """
    app_logger.info("Creating database and tables (if they don't exist)...")
    # Import models here so Base knows about them before creating tables
    from app.models.acl import Acl  # noqa: F401
    from app.models.activity import Activity  # noqa: F401
    from app.models.activity_group import ActivityGroup  # noqa: F401
    from app.models.activity_group_template import ActivityGroupTemplate  # noqa: F401
    from app.models.activity_template import ActivityTemplate  # noqa: F401
    from app.models.assessment import Assessment  # noqa: F401
    from app.models.asset import Asset  # noqa: F401
    from app.models.campaign_template import (  # noqa: F401
        CampaignTemplate,
        CampaignTemplateItem,
    )
    from app.models.evaluation_template import EvaluationTemplate  # noqa: F401
    from app.models.file import File  # noqa: F401
    from app.models.knowledge_base import KnowledgeBase  # noqa: F401
    from app.models.mitre import Tactic, Technique  # noqa: F401
    from app.models.report_template import ReportTemplate  # noqa: F401
    from app.models.tag import Tag  # noqa: F401
    from app.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    app_logger.info("Database and tables setup complete.")


def create_admin_user() -> None:
    """
    Called once at application startup to create the admin user.
    """
    with Session(engine) as session:
        if not check_user_exists_service(settings.ADMIN_EMAIL, session):
            app_logger.info("Creating admin user %s", settings.ADMIN_EMAIL)

            user_in = UserCreate(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                role=UserRole.ADMIN,
                disabled=False,
            )

            create_user_service(user_in, None, session)
        else:
            app_logger.info("Admin user already exists.")
