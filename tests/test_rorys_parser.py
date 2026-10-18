import logging
from datetime import date, datetime
from pathlib import Path

import pytest

from deal_dashboard.sources.rorys import OFFERS_URL, RorysOfferParser
from tests.helpers import make_card, parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_real_spencer_card(scraped_at: datetime) -> None:
    html = (FIXTURES / "rorys_card.html").read_text(encoding="utf-8")

    offers = parse(html, scraped_at=scraped_at)

    assert len(offers) == 1
    offer = offers[0]
    assert offer.source == "rorys"
    assert offer.name == "4* The Spencer Hotel"
    assert offer.description == "Sunday Night Special B&B, 2 course dinner with a cocktail, leisure access 2 Sharing From €215 | Solo from €175"
    assert offer.link == "https://rorystravelclub.com/pages/thespencerhoteldublin"
    assert offer.image_urls == ("https://rorystravelclub.com/cdn/shop/files/The_Spencer_hotel_1.jpg?v=1753790634&width=600",)
    assert offer.county == "dublin"
    assert offer.expiry == date(2026, 12, 13)
    assert offer.scraped_at == scraped_at
    assert "The Spencer Hotel" in offer.raw_html


def test_empty_page_returns_no_offers(scraped_at: datetime) -> None:
    assert parse("<html><body></body></html>", scraped_at=scraped_at) == []


def test_multiple_cards_each_become_one_offer(scraped_at: datetime) -> None:
    html = make_card(name="Hotel A") + make_card(name="Hotel B")

    names = [o.name for o in parse(html, scraped_at=scraped_at)]

    assert names == ["Hotel A", "Hotel B"]  # exactly 2: inner content divs are not cards


def test_card_without_name_is_skipped_and_logged(caplog: pytest.LogCaptureFixture, scraped_at: datetime) -> None:
    html = make_card(name=None) + make_card(name="Good Hotel")

    with caplog.at_level(logging.WARNING):
        offers = parse(html, scraped_at=scraped_at)

    assert [o.name for o in offers] == ["Good Hotel"]  # bad card didn't poison the good one
    assert "no name" in caplog.text


def test_missing_optional_fields_use_defaults(scraped_at: datetime) -> None:
    html = make_card(description=None, href=None, image_src=None, county=None, expiry=None)

    (offer,) = parse(html, scraped_at=scraped_at)

    assert offer.description == ""
    assert offer.link is None
    assert offer.image_urls == ()
    assert offer.county is None
    assert offer.expiry is None


@pytest.mark.parametrize("bad_value", ["", "TBC", "2026-13-45", "13/12/2026"])
def test_unparseable_expiry_becomes_none_without_crashing(bad_value: str, scraped_at: datetime) -> None:
    (offer,) = parse(make_card(expiry=bad_value), scraped_at=scraped_at)

    assert offer.expiry is None
    assert offer.name == "Test Hotel"  # rest of the card still parsed


def test_garbage_expiry_is_logged(caplog: pytest.LogCaptureFixture, scraped_at: datetime) -> None:
    with caplog.at_level(logging.WARNING):
        parse(make_card(expiry="TBC"), scraped_at=scraped_at)

    assert "TBC" in caplog.text


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("/pages/x", "https://rorystravelclub.com/pages/x"),  # root-relative
        ("https://other.test/y", "https://other.test/y"),  # absolute: untouched
        ("mailto:hi@example.test", "mailto:hi@example.test"),  # non-http: untouched
        ("tel:+35310000000", "tel:+35310000000"),
    ],
)
def test_link_resolution(href: str, expected: str, scraped_at: datetime) -> None:
    (offer,) = parse(make_card(href=href), scraped_at=scraped_at)
    assert offer.link == expected


def test_protocol_relative_image_gets_https(scraped_at: datetime) -> None:
    (offer,) = parse(make_card(image_src="//cdn.test/a.jpg"), scraped_at=scraped_at)
    assert offer.image_urls == ("https://cdn.test/a.jpg",)


def test_parser_is_deterministic(scraped_at: datetime) -> None:
    html = make_card()
    assert parse(html, scraped_at=scraped_at) == parse(html, scraped_at=scraped_at)  # pure: same input, same output (models are frozen, so == works)


def test_custom_source_name_is_used(scraped_at: datetime) -> None:
    parser = RorysOfferParser(source_name="other", base_url=OFFERS_URL)
    (offer,) = parser.parse(make_card(), scraped_at=scraped_at)
    assert offer.source == "other"


def test_full_leinster_page_regression(scraped_at: datetime) -> None:
    """Parses a real saved page. If the site changes, update the fixture AND these numbers."""
    html = (FIXTURES / "rorys_leinster_page.html").read_text(encoding="utf-8")

    offers = parse(html, scraped_at=scraped_at)

    assert len(offers) == 31
    assert all(o.name for o in offers)
    assert all(o.link is not None and o.link.startswith("https://") for o in offers)
    assert all(o.expiry is not None for o in offers)
    assert all(o.county for o in offers)
    assert len({o.link for o in offers}) == 31  # every card links to a distinct page
