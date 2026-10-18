"""Rory's Travel Club: parser and source.

The CSS selectors below are the ONLY place that knows what the site's HTML looks
like. When the site changes its layout, this block is what you edit.
"""

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from deal_dashboard.fetching import HtmlFetcher
from deal_dashboard.models import RawOffer
from deal_dashboard.sources.base import OfferSource

logger = logging.getLogger(__name__)

OFFERS_URL = "https://rorystravelclub.com/pages/offers25q1"
PAGE_EXTENSIONS = (
    "rtc-ulster-offers-1",  # Ulster
    "rtc-leinster-offers",  # Leinster
    "rtc-munster-offers",  # Munster
    "rtc-connacht-offers",  # Connacht
)


# --- Selectors: VERIFY THESE AGAINST THE REAL PAGE (see guide, section 2.2) ---
CARD_SELECTOR = "div[data-hotel]"
NAME_SELECTOR = '[class*="card-hotel"]'
DESCRIPTION_SELECTOR = '[class*="card-description"]'
EXPIRY_SELECTOR = "[data-expiry]"
LINK_SELECTOR = 'a[class*="card-button"]'
IMAGE_SELECTOR = 'img[class*="card-image"]'
# -----------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Collapse runs of whitespace (including newlines) to single spaces."""
    return " ".join(text.split())


def _text_of(card: Tag, selector: str) -> str:
    element = card.select_one(selector)
    return _clean(element.get_text(" ")) if element else ""


def _attr(tag: Tag, attribute: str) -> str | None:
    """Return an attribute as a string (bs4 may give a list for multi-valued attrs)."""
    value = tag.get(attribute)
    if isinstance(value, str):
        return value
    return None


def _parse_iso_date(value: str | None) -> date | None:
    """Parse 'YYYY-MM-DD'. Returns None (and logs) rather than raising on bad input."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        logger.warning("Unparseable expiry date: %r", value)
        return None


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RorysOfferParser:
    """Turns the offers page HTML into ``RawOffer`` objects. Pure: no network, no clock."""

    def __init__(self, source_name: str = "rorys", base_url: str = OFFERS_URL) -> None:
        self._source_name = source_name
        self._base_url = base_url

    def parse(self, html: str, scraped_at: datetime) -> list[RawOffer]:
        soup = BeautifulSoup(html, "html.parser")
        offers: list[RawOffer] = []
        for card in soup.select(CARD_SELECTOR):
            offer = self._parse_card(card, scraped_at)
            if offer is not None:
                offers.append(offer)
        logger.info("Parsed %d offers", len(offers))
        return offers

    def _parse_card(self, card: Tag, scraped_at: datetime) -> RawOffer | None:
        name = _text_of(card, NAME_SELECTOR)
        if not name:
            logger.warning("Skipping card with no name: %.80s", _clean(card.get_text(" ")))
            return None

        link_tag = card.select_one(LINK_SELECTOR)
        href = _attr(link_tag, "href") if link_tag else None
        link = urljoin(self._base_url, href) if href else None

        image_urls = tuple(urljoin(self._base_url, src) for image in card.select(IMAGE_SELECTOR) if (src := _attr(image, "src")))

        county = _attr(card, "data-county")

        expiry_tag = card.select_one(EXPIRY_SELECTOR)
        expiry = _parse_iso_date(_attr(expiry_tag, "data-expiry") if expiry_tag else None)

        return RawOffer(
            source=self._source_name,
            name=name,
            description=_text_of(card, DESCRIPTION_SELECTOR),
            expiry=expiry,
            county=county,
            link=link,
            image_urls=image_urls,
            scraped_at=scraped_at,
            raw_html=str(card),
        )


class RorysTravelClubSource(OfferSource):
    """Composes a fetcher and a parser. Both are injected, so both can be faked in tests."""

    def __init__(
        self,
        fetcher: HtmlFetcher,
        parser: RorysOfferParser | None = None,
        base_url: str = OFFERS_URL,
        extensions: tuple[str, ...] = PAGE_EXTENSIONS,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._fetcher = fetcher
        self._parser = parser or RorysOfferParser()
        self._base_url = base_url
        self._extensions = extensions
        self._clock = clock

    @property
    def name(self) -> str:
        return "rorys"

    def fetch_offers(self) -> list[RawOffer]:
        scraped_at = self._clock()  # one timestamp for the whole run
        offers: list[RawOffer] = []
        for ext in self._extensions:
            page_url = urljoin(self._base_url, ext)
            html = self._fetcher.fetch(page_url)
            page_offers = self._parser.parse(html, scraped_at=scraped_at)
            if not page_offers:
                logger.warning("No offers parsed from %s (has the layout changed?)", page_url)
            offers.extend(page_offers)
        return offers
