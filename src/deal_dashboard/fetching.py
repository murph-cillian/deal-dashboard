"""Getting HTML from the network, kept separate from interpreting it."""

from typing import Protocol

import requests

DEFAULT_USER_AGENT = "deal-dashboard/0.1 (personal hobby project)"


class HtmlFetcher(Protocol):
    """Anything that can turn a URL into HTML text.

    A Protocol is structural typing: any object with a matching ``fetch`` method
    qualifies, with no inheritance required. Tests pass in a fake.
    """

    def fetch(self, url: str) -> str: ...


class RequestsFetcher:
    """Fetches pages over HTTP using the ``requests`` library."""

    def __init__(
        self,
        session: requests.Session | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._timeout = timeout_seconds

    def fetch(self, url: str) -> str:
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.text
