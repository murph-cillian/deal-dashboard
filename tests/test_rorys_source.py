import pytest

from deal_dashboard.sources.base import OfferSource
from deal_dashboard.sources.rorys import PAGE_EXTENSIONS, RorysTravelClubSource
from tests.test_rorys_parser import make_card  # see note below


class FakeFetcher:
    """Satisfies HtmlFetcher structurally. Records requests, serves canned pages."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.requested: list[str] = []

    def fetch(self, url: str) -> str:
        self.requested.append(url)
        return self.pages[url]


def test_source_is_an_offer_source_with_stable_name() -> None:
    source = RorysTravelClubSource(FakeFetcher({}))
    assert isinstance(source, OfferSource)
    assert source.name == "rorys"


def test_fetches_every_regional_page_in_order() -> None:
    expected_urls = [f"https://rorystravelclub.com/pages/{ext}" for ext in PAGE_EXTENSIONS]
    fetcher = FakeFetcher({url: make_card() for url in expected_urls})

    RorysTravelClubSource(fetcher).fetch_offers()

    assert fetcher.requested == expected_urls


def test_combines_offers_from_all_pages() -> None:
    urls = ["https://example.test/pages/a", "https://example.test/pages/b"]
    fetcher = FakeFetcher({urls[0]: make_card(name="From A"), urls[1]: make_card(name="From B")})
    source = RorysTravelClubSource(fetcher, base_url="https://example.test/pages/start", extensions=("a", "b"))

    offers = source.fetch_offers()

    assert [o.name for o in offers] == ["From A", "From B"]


def test_scraped_at_is_timezone_aware() -> None:
    fetcher = FakeFetcher({f"https://rorystravelclub.com/pages/{ext}": make_card() for ext in PAGE_EXTENSIONS})

    offers = RorysTravelClubSource(fetcher).fetch_offers()

    assert all(o.scraped_at.tzinfo is not None for o in offers)


def test_fetch_error_propagates() -> None:
    class BrokenFetcher:
        def fetch(self, url: str) -> str:
            raise RuntimeError("network down")

    with pytest.raises(RuntimeError):
        RorysTravelClubSource(BrokenFetcher()).fetch_offers()
