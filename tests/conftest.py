"""Shared test setup.

Collector and Data Service tests never touch the network or the repository's real
``data/raw`` / ``data/snapshots`` / ``output`` directories.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from daily_market_snapshot import artifacts
from daily_market_snapshot.sources import tushare

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent


@pytest.fixture(autouse=True)
def test_workdir() -> Iterator[Path]:
    """A scratch directory for one test, removed afterwards.

    Layout previews and Raw Artifact files are written here instead of into the
    repository's real output directories.
    """
    path = Path(tempfile.mkdtemp(prefix="dms-test-", dir=REPO_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def raw_dir_in_test_workdir(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep collector output out of the repository's real ``data/raw``."""
    monkeypatch.setattr(artifacts, "RAW_DIR", test_workdir / "raw")


@pytest.fixture(autouse=True)
def snapshots_dir_in_test_workdir(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep snapshot output out of the repository's real ``data/snapshots``."""
    monkeypatch.setattr(artifacts, "SNAPSHOTS_DIR", test_workdir / "snapshots")


@pytest.fixture(autouse=True)
def output_dir_in_test_workdir(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep Data Service output out of the repository's real ``output/``."""
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", test_workdir / "output")


@pytest.fixture(autouse=True)
def no_local_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never read the developer's real ``.env`` during tests."""

    def fake_load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(tushare, "load_dotenv", fake_load_dotenv)
