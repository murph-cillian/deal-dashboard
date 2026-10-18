"""Saving raw HTML to disk, as a transparent layer around any HtmlFetcher."""

import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from deal_dashboard.fetching import HtmlFetcher

logger = logging.getLogger(__name__)


def save_snapshot(html: str, directory: Path, taken_at: datetime, label: str) -> Path:
    """Write raw HTML to ``<label>_<timestamp>.html`` and return the path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{label}_{taken_at:%Y%m%dT%H%M%SZ}.html"
    path.write_text(html, encoding="utf-8")
    return path


def _slug(url: str) -> str:
    """Last path segment of a URL: '.../pages/rtc-leinster-offers' -> 'rtc-leinster-offers'."""
    return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1] or "index"


class SnapshottingFetcher:
    """Decorator: wraps any HtmlFetcher, saves every page it fetches, returns the HTML unchanged.

    Because it has the same ``fetch`` method as the thing it wraps, the rest of the
    program can't tell it's there. That is the Decorator pattern: add behaviour
    without modifying (or even knowing about) the wrapped class.
    """

    def __init__(self, inner: HtmlFetcher, directory: Path, taken_at: datetime, prefix: str) -> None:
        self._inner = inner
        self._directory = directory
        self._taken_at = taken_at
        self._prefix = prefix

    def fetch(self, url: str) -> str:
        html = self._inner.fetch(url)
        path = save_snapshot(html, self._directory, self._taken_at, f"{self._prefix}_{_slug(url)}")
        logger.info("Saved snapshot of %s to %s", url, path)
        return html
