"""Domain models shared by every stage of the pipeline."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RawOffer(BaseModel):
    """An offer exactly as a source published it, with no interpretation.

    Parsing into structured prices is a later stage's job.
    Keeping the raw text means we can re-parse old data when
    that later stage improves.
    """

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Identifier of the site this came from, e.g. 'rorys'.")
    name: str = Field(min_length=1, description="Venue name as displayed.")
    headline: str = Field(description="The offer description text as displayed.")
    link: str | None = Field(default=None, description="Booking/more-info link (http, mailto or tel).")
    image_urls: tuple[str, ...] = Field(default=(), description="Image URLs shown on the card.")
    scraped_at: datetime = Field(description="When we fetched the page (timezone-aware, UTC).")
    raw_html: str = Field(description="The HTML of this single offer card, kept for re-parsing.")
