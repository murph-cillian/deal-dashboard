from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from deal_dashboard.models import RawOffer


def make_offer(**overrides: object) -> RawOffer:
    fields: dict[str, object] = {
        "source": "rorys",
        "name": "Test Hotel",
        "description": "B&B from €99",
        "scraped_at": datetime(2026, 10, 14, tzinfo=UTC),
        "raw_html": "<div></div>",
    }
    fields.update(overrides)
    return RawOffer.model_validate(fields)


def test_raw_offer_applies_defaults() -> None:
    offer = make_offer()
    assert offer.link is None
    assert offer.image_urls == ()
    assert offer.expiry is None
    assert offer.county is None


def test_raw_offer_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        make_offer(name="")


def test_raw_offer_is_immutable() -> None:
    offer = make_offer()
    with pytest.raises(ValidationError):
        offer.name = "Changed"


def test_raw_offer_accepts_iso_string_for_expiry() -> None:
    # Pydantic's default "lax" mode coerces ISO strings to dates.
    offer = make_offer(expiry="2026-12-13")
    assert offer.expiry == date(2026, 12, 13)


def test_raw_offer_rejects_invalid_expiry() -> None:
    # This is WHY the parser must guard against bad dates itself:
    # the model is strict, so one bad card would otherwise raise.
    with pytest.raises(ValidationError):
        make_offer(expiry="TBC")
