"""Backend and frontend launcher delegation checks."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ui_cli import cli, process, serve


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

    monkeypatch.setattr(process.subprocess, "Popen", fake_popen)
    return invocation


@pytest.mark.parametrize("exit_code", [0, 23])
def test_backend_uses_the_backend_api_launcher(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    invocation = patch_child(monkeypatch, exit_code)

    assert cli.main(["serve", "backend"]) == exit_code
    assert invocation == {
        "command": [sys.executable, "ui_http/scripts/api.py"],
        "cwd": serve.ROOT,
    }


@pytest.mark.parametrize("resolved_npm", ["/tools/npm", "C:/Tools/npm.cmd", "C:/Tools/npm.exe"])
@pytest.mark.parametrize("exit_code", [0, 23])
def test_frontend_uses_the_resolved_launcher(
    monkeypatch: pytest.MonkeyPatch, resolved_npm: str, exit_code: int
) -> None:
    invocation: dict[str, Any] = {}

    class FakeChild:
        def wait(self, timeout: int | None = None) -> int:
            assert timeout is None
            return exit_code

    def fake_popen(command: list[str], *, cwd: Path) -> FakeChild:
        invocation["command"] = command
        invocation["cwd"] = cwd
        return FakeChild()

    monkeypatch.setattr(
        process.shutil, "which", lambda name: resolved_npm if name == "npm" else None
    )
    monkeypatch.setattr(process.subprocess, "Popen", fake_popen)

    assert cli.main(["serve", "frontend"]) == exit_code
    assert invocation == {"command": [resolved_npm, "run", "dev"], "cwd": serve.FRONTEND}
