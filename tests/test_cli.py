import logging

import pytest

from deal_dashboard.cli import report
from tests.helpers import make_offer  # see note below


def test_report_returns_zero_when_offers_found() -> None:
    assert report([make_offer()]) == 0


def test_report_fails_loudly_when_no_offers(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        assert report([]) == 1
    assert "layout has probably changed" in caplog.text
