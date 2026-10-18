"""Local ignored state is preserved and split storage fails before acquisition."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from ui_cli import ROOT


def migration_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "local_migration", ROOT / ".codex/scripts/migrate_local_state.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_copy_preserves_sources_and_sqlite_companions(tmp_path: Path) -> None:
    source = tmp_path / "data-lake/datasets/fake/data"
    source.mkdir(parents=True)
    for name in ("fake.sqlite3", "fake.sqlite3-wal", "fake.sqlite3-shm"):
        (source / name).write_bytes(name.encode())
    credential = tmp_path / "market-snapshot/.env"
    credential.parent.mkdir()
    credential.write_bytes(b"FAKE_ONLY=fixture")
    tool = migration_tool()
    assert tool.migrate(tmp_path) == 4
    assert not (tmp_path / "data_lake").exists()
    assert tool.migrate(tmp_path, apply=True) == 4
    assert tool.migrate(tmp_path, apply=True) == 4
    for old in source.iterdir():
        new = tmp_path / "data_lake/datasets/fake/data" / old.name
        assert new.read_bytes() == old.read_bytes()
    assert credential.read_bytes() == (tmp_path / "data_snapshot/.env").read_bytes()


def test_conflict_stops_before_any_copy(tmp_path: Path) -> None:
    old = tmp_path / "market-snapshot"
    old.mkdir()
    (old / ".env").write_bytes(b"old fixture")
    (old / "data").mkdir()
    (old / "data/raw.json").write_bytes(b"original")
    target = tmp_path / "data_snapshot/data"
    target.mkdir(parents=True)
    (target / "raw.json").write_bytes(b"different")
    with pytest.raises(ValueError, match="Conflicting"):
        migration_tool().migrate(tmp_path, apply=True)
    assert not (target.parent / ".env").exists()
    assert (target / "raw.json").read_bytes() == b"different"
    assert (old / "data/raw.json").read_bytes() == b"original"
