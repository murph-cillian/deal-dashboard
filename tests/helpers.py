from datetime import UTC, datetime

from deal_dashboard.models import RawOffer
from deal_dashboard.sources.rorys import RorysOfferParser


def make_card(
    *,
    name: str | None = "Test Hotel",
    description: str | None = "B&amp;B from €99",
    href: str | None = "/pages/test-hotel",
    image_src: str | None = "//cdn.test/img.jpg",
    county: str | None = "dublin",
    expiry: str | None = "2026-12-13",
    data_id: str | None = "1928948678924",
) -> str:
    county_attr = f' data-county="{county}"' if county is not None else ""
    parts = [f'<div data-hotel="x"{county_attr}>']
    if expiry is not None or data_id is not None:
        id_attr = f' data-id="{data_id}"' if data_id is not None else ""
        expiry_attr = f' data-expiry="{expiry}"' if expiry is not None else ""
        parts.append(f'<button class="heart"{id_attr}{expiry_attr}></button>')

    if image_src is not None:
        parts.append(f'<img class="x-card-image-abc" src="{image_src}">')

    parts.append('<div class="x-card-content-abc">')  # inner div: must NOT count as a card
    if name is not None:
        parts.append(f'<h3 class="x-card-hotel-abc">{name}</h3>')

    if description is not None:
        parts.append(f'<p class="x-card-description-abc">{description}</p>')

    if href is not None:
        parts.append(f'<a class="x-card-button-abc" href="{href}">View Offer</a>')

    parts.append("</div></div>")
    return "".join(parts)


def parse(html: str, scraped_at: datetime) -> list[RawOffer]:
    return RorysOfferParser().parse(html, scraped_at=scraped_at)


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
