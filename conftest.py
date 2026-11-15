"""Repository-wide test isolation for local configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

import lab_config

# Manual diagnostics are excluded before import (notably Linux-only deploy tooling).
DIAGNOSTIC_FILES = {
    "data_snapshot/tests/test_authority_topology.py",
    "ui_http/tests/test_architecture.py",
    "market_backtesting/tests/test_architecture.py",
    "market_statistics/tests/test_statistics_architecture.py",
    "data_lake/providers/tushare/tests/test_provider_topology.py",
    "data_lake/datasets/tushare_trade_calendar/tests/test_topology.py",
    "ui_http/tests/test_auth_tls.py",
}
ROOT = Path(__file__).resolve().parent


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--diagnostics", action="store_true", help="Explicitly enable manual diagnostics"
    )


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if config.getoption("--diagnostics"):
        return None
    if not collection_path.is_relative_to(ROOT):
        return None
    relative = collection_path.relative_to(ROOT).as_posix()
    if relative in DIAGNOSTIC_FILES or relative == "ui_web/tests/deploy":
        return True
    return None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        path = item.path.relative_to(ROOT).as_posix()
        if path in DIAGNOSTIC_FILES or path.startswith("ui_web/tests/deploy/"):
            item.add_marker(pytest.mark.diagnostic)
    if config.getoption("--diagnostics"):
        return
    selected = [item for item in items if item.get_closest_marker("diagnostic") is None]
    excluded = [item for item in items if item.get_closest_marker("diagnostic") is not None]
    config.hook.pytest_deselected(items=excluded)
    items[:] = selected


@pytest.fixture(autouse=True)
def isolated_repository_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Never read the developer's real repository-root ``.env`` during tests."""
    monkeypatch.setattr(lab_config, "ENV_FILE", tmp_path / "absent.env")
