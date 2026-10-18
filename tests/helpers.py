from datetime import datetime

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
) -> str:
    """Build one offer card. Pass None to omit a part entirely."""
    county_attr = f' data-county="{county}"' if county is not None else ""
    parts = [f'<div data-hotel="x"{county_attr}>']
    if expiry is not None:
        parts.append(f'<button class="heart" data-expiry="{expiry}"></button>')
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


def parse(html: str, scraped_at: datetime) -> list[RawOffer]:  # see note below on typing
    return RorysOfferParser().parse(html, scraped_at=scraped_at)
