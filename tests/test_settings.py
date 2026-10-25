from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from deal_dashboard.settings import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run in an empty folder (so no real .env is read) with the variable unset."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEAL_DASHBOARD_DATABASE_URL", raising=False)


def test_default_database_url_is_used_when_nothing_is_set() -> None:
    assert Settings().database_url == "sqlite:///data/deal_dashboard.db"


def test_environment_variable_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEAL_DASHBOARD_DATABASE_URL", "sqlite:///custom.db")
    assert Settings().database_url == "sqlite:///custom.db"


def test_env_file_is_read(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("DEAL_DASHBOARD_DATABASE_URL=sqlite:///from_file.db\n", encoding="utf-8")
    assert Settings().database_url == "sqlite:///from_file.db"


def test_explicit_argument_beats_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEAL_DASHBOARD_DATABASE_URL", "sqlite:///from_env.db")
    assert Settings(database_url="sqlite://").database_url == "sqlite://"


def test_a_field_with_no_default_is_required() -> None:
    class NeedsKey(BaseSettings):
        api_key: str

    with pytest.raises(ValidationError):
        NeedsKey()  # pyright: ignore[reportCallIssue]
