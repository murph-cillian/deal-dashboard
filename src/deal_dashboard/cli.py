"""Command-line entry point. The composition root: the only place that builds the object graph."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from deal_dashboard.fetching import RequestsFetcher
from deal_dashboard.models import RawOffer
from deal_dashboard.snapshots import SnapshottingFetcher
from deal_dashboard.sources.rorys import RorysTravelClubSource

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = Path("data/raw")


def report(offers: list[RawOffer]) -> int:
    """Print a summary and return a process exit code (non-zero if nothing was parsed)."""
    for offer in offers:
        print(f"{offer.name}")
    print(f"\n{len(offers)} offers parsed.")
    if not offers:
        logger.error("Parsed 0 offers: the site layout has probably changed.")
        return 1
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_at = datetime.now(UTC)

    fetcher = SnapshottingFetcher(RequestsFetcher(), SNAPSHOT_DIR, run_at, prefix="rorys")
    source = RorysTravelClubSource(fetcher, clock=lambda: run_at)

    return report(source.fetch_offers())
