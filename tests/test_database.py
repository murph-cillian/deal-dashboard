from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from deal_dashboard.models import OfferStatus, RunStatus
from deal_dashboard.storage.database import make_engine
from deal_dashboard.storage.orm import Base, ObservationRow, OfferRow, ScrapeRunRow


def _run(when: datetime) -> ScrapeRunRow:
    return ScrapeRunRow(source="rorys", started_at=when, status=RunStatus.RUNNING)


def test_aware_datetime_round_trips_as_utc(session: Session) -> None:
    plus_one = timezone(timedelta(hours=1))
    session.add(_run(datetime(2026, 10, 18, 13, 0, tzinfo=plus_one)))
    session.commit()
    session.expire_all()

    stored = session.query(ScrapeRunRow).one().started_at

    assert stored.tzinfo is not None
    assert stored == datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def test_naive_datetime_is_rejected(session: Session) -> None:
    session.add(_run(datetime(2026, 10, 18, 12, 0)))
    with pytest.raises(Exception, match="naive datetime"):
        session.commit()


def test_foreign_keys_are_enforced(session: Session) -> None:
    session.add(
        ObservationRow(
            offer_id=999,
            scrape_run_id=999,
            scraped_at=datetime(2026, 10, 18, tzinfo=UTC),
            name="x",
            description="x",
            image_urls=[],
            raw_html="x",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_source_offer_id_is_rejected(session: Session) -> None:
    now = datetime(2026, 10, 18, tzinfo=UTC)
    for _ in range(2):
        session.add(OfferRow(source="rorys", source_offer_id="1", first_seen_at=now, last_seen_at=now, status=OfferStatus.ACTIVE))
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_observation_for_same_offer_and_run_is_rejected(session: Session) -> None:
    now = datetime(2026, 10, 18, tzinfo=UTC)
    offer = OfferRow(source="rorys", source_offer_id="1", first_seen_at=now, last_seen_at=now, status=OfferStatus.ACTIVE)
    run = _run(now)
    session.add_all([offer, run])
    session.flush()
    for _ in range(2):
        session.add(ObservationRow(offer_id=offer.id, scrape_run_id=run.id, scraped_at=now, name="x", description="x", image_urls=[], raw_html="x"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_file_database_creates_missing_folder_and_uses_wal(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "dir" / "test.db"
    engine = make_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
    engine.dispose()

    assert db_file.exists()
    assert mode == "wal"
    assert foreign_keys == 1
