"""Repository-wide test isolation for local configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

import lab_config


@pytest.fixture(autouse=True)
def isolated_repository_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Never read the developer's real repository-root ``.env`` during tests."""
    monkeypatch.setattr(lab_config, "ENV_FILE", tmp_path / "absent.env")
