from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from deal_dashboard.models import RawOffer


def make_offer(**overrides: object) -> RawOffer:
    fields: dict[str, object] = {
        "source": "rorys",
        "name": "Test Hotel",
        "headline": "B&B from €99",
        "scraped_at": datetime(2026, 10, 14, tzinfo=UTC),
        "raw_html": "<div></div>",
    }
    fields.update(overrides)
    return RawOffer.model_validate(fields)


def test_raw_offer_applies_defaults() -> None:
    offer = make_offer()
    assert offer.link is None
    assert offer.image_urls == ()


def test_raw_offer_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        make_offer(name="")


def test_raw_offer_is_immutable() -> None:
    offer = make_offer()
    with pytest.raises(ValidationError):
        offer.name = "Changed"
