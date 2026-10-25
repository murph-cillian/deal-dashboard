"""Engine creation and column types shared by all tables."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import DateTime, create_engine, event
from sqlalchemy.engine import Dialect, Engine, make_url
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """A datetime column that stores UTC, refuses naive datetimes and returns aware ones.

    SQLite has no real datetime type and hands back naive values, so we
    enforce our "always timezone-aware UTC" rule in one place.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime: use a timezone-aware UTC datetime")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return value.replace(tzinfo=UTC) if value is not None else None


def _sqlite_file_path(url: str) -> Path | None:
    """Return the file path for a file-based SQLite URL, or None for in-memory / other databases."""
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or not parsed.database or parsed.database == ":memory:":
        return None
    return Path(parsed.database)


def make_engine(url: str) -> Engine:
    """Create an engine. For SQLite: enforce foreign keys, and use WAL for file databases."""
    db_path = _sqlite_file_path(url)
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)  # SQLite creates the file, but not the folder

    engine = create_engine(url)

    if engine.dialect.name == "sqlite":
        use_wal = db_path is not None

        @event.listens_for(engine, "connect")
        def _configure_sqlite(dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")  # SQLite ignores foreign keys unless asked, per connection
            if use_wal:
                cursor.execute("PRAGMA journal_mode=WAL")  # lets a reader (the dashboard) work while a writer runs
            cursor.close()

    return engine
