"""Read-only repository diagnostics checks."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from ui_cli import doctor


@pytest.mark.parametrize("resolved_tool", ["/tools/npm", "C:/Tools/npm.cmd", "C:/Tools/npm.exe"])
def test_tool_version_uses_platform_resolved_executable(
    monkeypatch: pytest.MonkeyPatch, resolved_tool: str
) -> None:
    invocation: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        invocation["command"] = command
        invocation["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="test version", stderr="")

    monkeypatch.setattr(
        doctor, "resolve_executable", lambda name: resolved_tool if name == "npm" else None
    )
    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    assert doctor._tool_version("npm") == (resolved_tool, "test version")
    assert invocation["command"] == [resolved_tool, "--version"]
    assert "shell" not in invocation["kwargs"]


def test_doctor_inspects_current_root_python_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_tool_version(name: str) -> tuple[str, str]:
        return f"/tools/{name}", f"{name} test version"

    monkeypatch.setattr(doctor, "_tool_version", fake_tool_version)
    monkeypatch.setattr(
        doctor, "sys", SimpleNamespace(prefix=str(doctor.ROOT / ".venv"), version_info=(3, 13, 15))
    )
    monkeypatch.setattr(doctor, "_backend_status", lambda: "stopped")
    monkeypatch.setattr(doctor, "_port_listening", lambda port: False)

    assert doctor.doctor() == 0


def test_doctor_rejects_another_python_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(doctor, "_tool_version", lambda name: (name, "test version"))
    monkeypatch.setattr(
        doctor,
        "sys",
        SimpleNamespace(prefix=str(doctor.ROOT / "other-venv"), version_info=(3, 13, 15)),
    )
    monkeypatch.setattr(doctor, "_backend_status", lambda: "stopped")
    monkeypatch.setattr(doctor, "_port_listening", lambda port: False)

    assert doctor.doctor() == 1
    assert "current Python is not root .venv" in capsys.readouterr().out
