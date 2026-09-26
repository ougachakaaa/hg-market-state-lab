"""Tests for the repository-level Data Service convenience command."""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEV_PATH = REPOSITORY_ROOT / "dev.py"
POETRY = str(REPOSITORY_ROOT / "tools" / "poetry")
SERVICE_ID = "csi1000-5d-analysis"
TARGET_DATE = "2026-09-18"


def load_dev_module() -> Any:
    spec = importlib.util.spec_from_file_location("repository_dev", DEV_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dev: ModuleType | Any = load_dev_module()


def patch_child(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> dict[str, Any]:
    invocation: dict[str, Any] = {}

    class FakeChild:
        def wait(self, timeout: int | None = None) -> int:
            assert timeout is None
            return exit_code

    def fake_popen(command: list[str], *, cwd: Path) -> FakeChild:
        invocation["command"] = command
        invocation["cwd"] = cwd
        return FakeChild()

    monkeypatch.setattr(dev.shutil, "which", lambda name: POETRY if name == "poetry" else None)
    monkeypatch.setattr(dev.subprocess, "Popen", fake_popen)
    return invocation


def test_backend_uses_the_backend_api_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    invocation = patch_child(monkeypatch, 0)

    assert dev.main(["backend"]) == 0
    assert invocation == {
        "command": [POETRY, "run", "python", "scripts/api.py"],
        "cwd": dev.BACKEND_API,
    }


def test_data_requires_service_id() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev.main(["data"])

    assert excinfo.value.code == 2


@pytest.mark.parametrize("service_id", ["mo-option-chain", "no-such-service"])
def test_data_rejects_non_cli_and_unknown_services_before_process_start(
    monkeypatch: pytest.MonkeyPatch, service_id: str
) -> None:
    def unreachable(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("unsupported services must fail before process invocation")

    monkeypatch.setattr(dev.subprocess, "Popen", unreachable)

    with pytest.raises(SystemExit) as excinfo:
        dev.main(["data", service_id, "--date", TARGET_DATE])

    assert excinfo.value.code == 2


@pytest.mark.parametrize("exit_code", [0, 23])
def test_explicit_date_forms_dms_command_and_propagates_child_exit_code(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    invocation = patch_child(monkeypatch, exit_code)

    assert dev.main(["data", SERVICE_ID, "--date", TARGET_DATE]) == exit_code
    assert invocation == {
        "command": [
            POETRY,
            "run",
            "python",
            "scripts/dms.py",
            "get",
            SERVICE_ID,
            "--date",
            TARGET_DATE,
        ],
        "cwd": dev.MARKET_SNAPSHOT,
    }


def test_default_date_uses_asia_shanghai_calendar_day_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    utc_instant = datetime(2026, 9, 19, 16, 30, tzinfo=UTC)

    class FixedDateTime:
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            assert tz is dev.CHINA_MARKET_TIMEZONE
            return utc_instant.astimezone(tz)

    monkeypatch.setattr(dev, "datetime", FixedDateTime)
    invocation = patch_child(monkeypatch, 0)

    assert dev.main(["data", SERVICE_ID]) == 0
    assert invocation["command"][-2:] == ["--date", "2026-09-20"]
