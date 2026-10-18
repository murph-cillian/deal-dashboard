from datetime import UTC, datetime
from pathlib import Path

from deal_dashboard.cli import save_snapshot


def test_save_snapshot_writes_timestamped_file(tmp_path: Path) -> None:
    when = datetime(2026, 10, 14, 12, 30, 5, tzinfo=UTC)

    path = save_snapshot("<html>x</html>", tmp_path / "raw", when)

    assert path.name == "rorys_20261014T123005Z.html"
    assert path.read_text(encoding="utf-8") == "<html>x</html>"
