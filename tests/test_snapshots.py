from datetime import UTC, datetime
from pathlib import Path

from deal_dashboard.snapshots import SnapshottingFetcher, save_snapshot

WHEN = datetime(2026, 10, 14, 12, 30, 5, tzinfo=UTC)


class FakeFetcher:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    def fetch(self, url: str) -> str:
        return self.pages[url]


def test_save_snapshot_writes_labelled_timestamped_file(tmp_path: Path) -> None:
    path = save_snapshot("<html>x</html>", tmp_path / "raw", WHEN, "rorys_leinster")

    assert path.name == "rorys_leinster_20261014T123005Z.html"
    assert path.read_text(encoding="utf-8") == "<html>x</html>"


def test_snapshotting_fetcher_returns_html_unchanged_and_saves_it(tmp_path: Path) -> None:
    url = "https://example.test/pages/rtc-leinster-offers"
    fetcher = SnapshottingFetcher(FakeFetcher({url: "<p>hi</p>"}), tmp_path, WHEN, prefix="rorys")

    assert fetcher.fetch(url) == "<p>hi</p>"

    saved = tmp_path / "rorys_rtc-leinster-offers_20261014T123005Z.html"
    assert saved.read_text(encoding="utf-8") == "<p>hi</p>"


def test_each_page_gets_its_own_file(tmp_path: Path) -> None:
    pages = {"https://example.test/pages/a": "A", "https://example.test/pages/b": "B"}
    fetcher = SnapshottingFetcher(FakeFetcher(pages), tmp_path, WHEN, prefix="rorys")

    for url in pages:
        fetcher.fetch(url)

    assert len(list(tmp_path.glob("*.html"))) == 2
