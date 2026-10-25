"""SQLAlchemy table definitions. Persistence only: nothing outside storage/ should import these."""

from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from deal_dashboard.models import OfferStatus, RunStatus
from deal_dashboard.storage.database import UTCDateTime


class Base(DeclarativeBase):
    """Parent of every table class; Base.metadata is the catalogue Alembic reads."""


class ScrapeRunRow(Base):
    """One execution of a scrape."""

    __tablename__ = "scrape_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str]
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    status: Mapped[RunStatus]
    offers_parsed: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(default=None)


class OfferRow(Base):
    """The identity and lifecycle of one listing."""

    __tablename__ = "offer"
    __table_args__ = (UniqueConstraint("source", "source_offer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str]
    source_offer_id: Mapped[str]
    first_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[OfferStatus] = mapped_column(default=OfferStatus.ACTIVE)

    observations: Mapped[list["ObservationRow"]] = relationship(back_populates="offer")


class ObservationRow(Base):
    """What one card looked like in one run. Append-only: never updated."""

    __tablename__ = "observation"
    __table_args__ = (UniqueConstraint("offer_id", "scrape_run_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offer.id"), index=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_run.id"), index=True)
    scraped_at: Mapped[datetime] = mapped_column(UTCDateTime)
    name: Mapped[str]
    description: Mapped[str]
    expiry: Mapped[date | None]
    county: Mapped[str | None]
    link: Mapped[str | None]
    image_urls: Mapped[list[str]] = mapped_column(JSON)
    raw_html: Mapped[str]

    offer: Mapped["OfferRow"] = relationship(back_populates="observations")
