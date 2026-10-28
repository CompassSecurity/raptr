from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine, inspect

from app.core.startup import get_alembic_config, run_database_migrations
from app.models.base import Base


@pytest.fixture(name="migration_engine")
def migration_engine_fixture(tmp_path: Path) -> Generator[Engine, None, None]:
    """
    An empty SQLite database file, separate from the test suite's in-memory DB
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    yield engine
    engine.dispose()


def _head_revision() -> str | None:
    return ScriptDirectory.from_config(get_alembic_config()).get_current_head()


def _current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_migrations_create_schema_matching_models(migration_engine: Engine):
    """
    All migrations together must produce exactly the schema of the models.
    Fails when a model was changed without adding a migration.
    """
    run_database_migrations(migration_engine)

    with migration_engine.connect() as connection:
        differences = compare_metadata(
            MigrationContext.configure(connection), Base.metadata
        )
    assert differences == []
    assert _current_revision(migration_engine) == _head_revision()


def test_migrations_are_idempotent(migration_engine: Engine):
    """
    Starting the app again on an up-to-date database applies nothing
    """
    run_database_migrations(migration_engine)
    run_database_migrations(migration_engine)

    assert _current_revision(migration_engine) == _head_revision()


def test_downgrade_and_upgrade_again(migration_engine: Engine):
    """
    Downgrading to the start removes all tables; upgrading again works
    """
    run_database_migrations(migration_engine)

    alembic_config = get_alembic_config()
    with migration_engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        command.downgrade(alembic_config, "base")
    assert inspect(migration_engine).get_table_names() == ["alembic_version"]
    assert _current_revision(migration_engine) is None

    run_database_migrations(migration_engine)
    assert _current_revision(migration_engine) == _head_revision()


def test_old_database_is_refused(migration_engine: Engine):
    """
    A database created before migration support (tables, no alembic_version)
    is refused with a clear message and left untouched
    """
    Base.metadata.create_all(migration_engine)

    with pytest.raises(RuntimeError, match="without migration support"):
        run_database_migrations(migration_engine)
    assert "alembic_version" not in inspect(migration_engine).get_table_names()
