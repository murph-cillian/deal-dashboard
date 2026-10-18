"""The contract every deal source must satisfy."""

from abc import ABC, abstractmethod

from deal_dashboard.models import RawOffer


class OfferSource(ABC):
    """A website (or API) that can supply offers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short, stable identifier, stored on every offer from this source."""

    @abstractmethod
    def fetch_offers(self) -> list[RawOffer]:
        """Fetch and return the currently listed offers."""
