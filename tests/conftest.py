"""Shared test setup.

Collector tests never touch the network or the repository's real ``data/raw``.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _common  # noqa: E402


@pytest.fixture(autouse=True)
def test_workdir() -> Iterator[Path]:
    """A scratch directory for one test, removed afterwards.

    Layout previews and Raw Dataset files are written here instead of into the
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
    monkeypatch.setattr(_common, "RAW_DIR", test_workdir / "raw")


@pytest.fixture(autouse=True)
def no_local_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never read the developer's real ``.env`` during tests."""

    def fake_load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(_common, "load_dotenv", fake_load_dotenv)
