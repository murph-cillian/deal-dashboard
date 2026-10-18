import pytest
import requests

from deal_dashboard.fetching import DEFAULT_USER_AGENT, RequestsFetcher


class FakeResponse:
    def __init__(self, text: str, status: int = 200) -> None:
        self.text = text
        self._status = status

    def raise_for_status(self) -> None:
        if self._status >= 400:
            raise requests.HTTPError(f"{self._status} error")


def test_fetch_returns_response_text(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, float]] = []

    def fake_get(self: requests.Session, url: str, timeout: float) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse("<html>hi</html>")

    monkeypatch.setattr(requests.Session, "get", fake_get)

    fetcher = RequestsFetcher(timeout_seconds=5)
    assert fetcher.fetch("https://example.test") == "<html>hi</html>"
    assert calls == [("https://example.test", 5)]


def test_fetch_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(self: requests.Session, url: str, timeout: float) -> FakeResponse:
        return FakeResponse("nope", status=503)

    monkeypatch.setattr(requests.Session, "get", fake_get)

    with pytest.raises(requests.HTTPError):
        RequestsFetcher().fetch("https://example.test")


def test_fetcher_identifies_itself() -> None:
    session = requests.Session()
    RequestsFetcher(session=session)
    assert session.headers["User-Agent"] == DEFAULT_USER_AGENT
