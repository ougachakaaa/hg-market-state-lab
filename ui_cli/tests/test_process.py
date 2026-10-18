"""Shared foreground process behavior checks."""

from __future__ import annotations

import pytest

from ui_cli import ROOT, process


def test_foreground_interrupt_reaps_child(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[int | None] = []

    class FakeChild:
        def wait(self, timeout: int | None = None) -> int:
            waits.append(timeout)
            if timeout is None:
                raise KeyboardInterrupt
            return 130

    monkeypatch.setattr(process.subprocess, "Popen", lambda command, *, cwd: FakeChild())
    assert process.run_foreground(["command"], ROOT) == 130
    assert waits == [None, 2]
