"""Legacy Raw state must not be treated as a new empty checkout."""

from pathlib import Path

import pytest

from data_snapshot import artifacts
from data_snapshot.sources import tushare


def test_legacy_raw_stops_source_and_artifact_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy = tmp_path / "market-snapshot/data/raw"
    legacy.mkdir(parents=True)
    (legacy / "fixture.json").write_text("[]")
    monkeypatch.setattr(artifacts, "REPO_ROOT", tmp_path / "data_snapshot")
    monkeypatch.setenv("TUSHARE_TOKEN", "fake-fixture-only")
    with pytest.raises(tushare.TushareSourceError, match="LOCAL_MIGRATION"):
        tushare.get_tushare_token()
    with pytest.raises(OSError, match="LOCAL_MIGRATION"):
        artifacts.write_raw_artifact([], tmp_path / "data_snapshot/data/raw", "fixture")
    assert not (tmp_path / "data_snapshot").exists()
    assert (legacy / "fixture.json").read_text() == "[]"
