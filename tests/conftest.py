from datetime import UTC, datetime

import pytest


@pytest.fixture
def scraped_at() -> datetime:
    return datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
