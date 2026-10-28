import secrets
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import app_logger
from app.core.password import generate_secure_password
from app.db.session import engine
from app.enums.enums import UserRole
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


def run_database_migrations() -> None:
    """
    Called once at application startup to bring the database schema up to date
    by applying all pending migrations (on an empty database this creates all tables).
    """
    # A database with tables but without alembic_version was created by a version
    # before migration support; it can't be migrated and must be recreated
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
    if table_names and "alembic_version" not in table_names:
        message = (
            "The database was created by a RAPTR version without migration support "
            "and can't be upgraded. Back it up if needed, then start RAPTR with an "
            "empty database; it will be set up again."
        )
        app_logger.critical(message)
        raise RuntimeError(message)

    # Configured in code (no alembic.ini needed at runtime)
    alembic_config = Config()
    alembic_config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "db" / "migrations")
    )

    app_logger.info("Applying database migrations...")
    command.upgrade(alembic_config, "head")
    app_logger.info("Database migrations complete.")


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
