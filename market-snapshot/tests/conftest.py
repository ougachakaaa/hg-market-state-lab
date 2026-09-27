"""Shared test setup.

Capture and Product tests never touch the network or the repository's real
``data/raw`` directory.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from market_snapshot import artifacts
from market_snapshot.sources import tushare

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent


@pytest.fixture(autouse=True)
def test_workdir() -> Iterator[Path]:
    """A scratch directory for one test, removed afterwards.

    Raw Artifact files are written here instead of into the repository's real
    data directory.
    """
    path = Path(tempfile.mkdtemp(prefix="snapshot-test-", dir=REPO_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def raw_dir_in_test_workdir(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep Capture output out of the repository's real ``data/raw``."""
    monkeypatch.setattr(artifacts, "RAW_DIR", test_workdir / "raw")


@pytest.fixture(autouse=True)
def no_local_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never read the developer's real ``.env`` during tests."""

    def fake_load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(tushare, "load_dotenv", fake_load_dotenv)
