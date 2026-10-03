"""Shared Research output placement and transactional publication checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_research.ui.execution import (
    ResearchOutputError,
    canonical_run_directory,
    execute_run,
)


def test_publication_failure_restores_previous_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = canonical_run_directory(
        tmp_path, "example-study", "2025-01-01__2025-02-01"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve me", encoding="utf-8")

    def execute(output: Path) -> tuple[Path, ...]:
        artifact = output / "new.txt"
        artifact.write_text("new", encoding="utf-8")
        return (artifact,)

    original_rename = Path.rename
    calls = 0

    def fail_publish(path: Path, target: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publish failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_publish)

    with pytest.raises(ResearchOutputError, match="simulated publish failure"):
        execute_run(execute, run_dir, overwrite=True)

    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve me"


def test_opaque_run_keys_have_deterministic_distinct_placements(tmp_path: Path) -> None:
    first = canonical_run_directory(tmp_path, "example-study", "window~20__method-a")
    assert first == tmp_path / "example-study" / "window~20__method-a"
    assert first == canonical_run_directory(tmp_path, "example-study", "window~20__method-a")
    assert first != canonical_run_directory(tmp_path, "example-study", "window~20__method-b")


@pytest.mark.parametrize(
    "run_key",
    [
        "", ".", "..", "../outside", "nested/path", r"nested\path",
        "/absolute", r"C:\absolute", "CON", "trailing.",
    ],
)
def test_unsafe_run_keys_are_rejected(tmp_path: Path, run_key: str) -> None:
    with pytest.raises(ResearchOutputError, match="unsafe run key"):
        canonical_run_directory(tmp_path, "example-study", run_key)


def test_symlinked_study_and_run_locations_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "output"
    root.mkdir()
    try:
        (root / "example-study").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314:
            raise
        pytest.skip(f"symlink creation unavailable: {exc}")
    with pytest.raises(ResearchOutputError, match="symlink"):
        canonical_run_directory(root, "example-study", "run")
    (root / "example-study").unlink()
    study = root / "example-study"
    study.mkdir()
    (study / "run").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ResearchOutputError, match="symlink"):
        canonical_run_directory(root, "example-study", "run")


def test_opaque_run_collision_fails_before_execute(tmp_path: Path) -> None:
    run_dir = canonical_run_directory(tmp_path, "example-study", "opaque-key")
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve me", encoding="utf-8")

    def execute(_output: Path) -> tuple[Path, ...]:
        raise AssertionError("execution must not start")

    with pytest.raises(ResearchOutputError, match="already exists"):
        execute_run(execute, run_dir, overwrite=False)
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve me"


def test_research_ui_does_not_import_snapshot_internals() -> None:
    research_root = Path(__file__).resolve().parents[1]
    sources = [
        research_root / "ui/src/market_research/ui/configuration.py",
        research_root / "ui/src/market_research/ui/execution.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    for forbidden in (
        "market_snapshot.sources",
        "market_snapshot.capture",
        "TushareApi",
        "TUSHARE_TOKEN",
        "backend_api",
    ):
        assert forbidden not in source
