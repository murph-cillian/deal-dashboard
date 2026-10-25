"""Alembic environment: points migrations at our models and at the database named in Settings."""

from logging.config import fileConfig
from typing import Literal

from alembic import context
from alembic.autogenerate.api import AutogenContext

from deal_dashboard.settings import Settings
from deal_dashboard.storage.database import UTCDateTime, make_engine
from deal_dashboard.storage.orm import Base

config = context.config

if config.config_file_name is not None:
    # disable_existing_loggers=False: otherwise Alembic silences our app's loggers (and breaks caplog in tests).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def render_item(type_: str, obj: object, autogen_context: AutogenContext) -> str | Literal[False]:
    """Write our custom column type as a plain SQLAlchemy type.

    A migration is a frozen snapshot of the schema at one moment. It must not import
    application code that will change later, so UTCDateTime is stored as sa.DateTime().
    """
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime()"
    return False


def get_url() -> str:
    """A URL set on the Alembic config (tests do this) wins; otherwise use the application's Settings."""
    return config.get_main_option("sqlalchemy.url") or Settings().database_url


def run_migrations_offline() -> None:
    """Emit SQL to the console without connecting ('alembic upgrade head --sql')."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and run migrations."""
    engine = make_engine(get_url())
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite can't ALTER columns in place; batch mode rebuilds the table instead
            render_item=render_item,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
