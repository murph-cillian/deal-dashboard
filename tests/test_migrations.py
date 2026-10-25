from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def alembic_config(tmp_path: Path) -> Config:
    """An Alembic config pointed at a throwaway database file."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path / 'test.db'}")
    return config


def table_names(config: Config) -> set[str]:
    engine = create_engine(config.get_main_option("sqlalchemy.url") or "")
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_upgrade_head_creates_the_core_tables(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")

    assert {"scrape_run", "offer", "observation"} <= table_names(alembic_config)


def test_models_and_migrations_agree(alembic_config: Config) -> None:
    """Fails if you changed orm.py but forgot to write a migration ('alembic check')."""
    command.upgrade(alembic_config, "head")

    command.check(alembic_config)  # raises if autogenerate would produce any change


def test_downgrade_to_base_removes_the_tables(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")

    assert table_names(alembic_config) <= {"alembic_version"}
