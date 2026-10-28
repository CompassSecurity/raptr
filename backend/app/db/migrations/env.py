"""
Alembic migration environment.

Runs migrations against the app's own database (same settings and engine as the
app) and compares that database with the SQLAlchemy models for autogenerate.
"""

from logging.config import fileConfig

from alembic import context

from app.core.config import settings
from app.db.session import DATABASE_URL, engine

# Every model file in app/models must be imported here. Alembic only sees the
# tables of loaded models: a missing import makes autogenerate propose dropping
# that table (and its data).
from app.models import (  # noqa: F401
    acl,
    activity,
    activity_evaluation,
    activity_evaluation_dynamic_questions,
    activity_group,
    activity_group_template,
    activity_history,
    activity_template,
    assessment,
    asset,
    campaign_template,
    evaluation_template,
    file,
    knowledge_base,
    mitre,
    report_template,
    tag,
    user,
)
from app.models.base import Base

config = context.config

# Logging from alembic.ini when run from the command line. When the app runs the
# migrations itself there is no ini file, so the app's logging stays untouched.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# SQLite can't alter most table properties in place; batch mode recreates the table
render_as_batch = settings.DB_ENGINE == "sqlite"


def run_migrations_offline() -> None:
    """Write the migration SQL instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run the migrations on the app's database, using the app's engine."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
