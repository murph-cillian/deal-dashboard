"""Command-line entry point: fetch the page, save a raw snapshot, print a summary."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from deal_dashboard.fetching import RequestsFetcher
from deal_dashboard.sources.rorys import RorysOfferParser

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = Path("data/raw")
OFFERS_URL = "https://rorystravelclub.com/pages/rtc-leinster-offers"  # Leinster offers page


def save_snapshot(html: str, directory: Path, scraped_at: datetime) -> Path:
    """Write the raw HTML to a timestamped file and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"rorys_{scraped_at:%Y%m%dT%H%M%SZ}.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    now = datetime.now(UTC)
    html = RequestsFetcher().fetch(OFFERS_URL)
    snapshot = save_snapshot(html, SNAPSHOT_DIR, now)
    logger.info("Saved raw snapshot to %s", snapshot)

    offers = RorysOfferParser().parse(html, scraped_at=now)
    for offer in offers:
        print(f"{offer.name}")
    print(f"\n{len(offers)} offers parsed.")
    return 0
