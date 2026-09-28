"""Repository Research discovery and forwarding checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from lab import cli, process, research

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STUDY_IDS = (
    "im-basis-baseline",
    "im-basis-forward-return-association",
    "price-to-lagged-ma-distribution",
)


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


def create_study_package(root: Path, package_name: str, *, runner: bool = True) -> Path:
    package = root / package_name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if runner:
        (package / "cli.py").write_text("", encoding="utf-8")
    return package


@pytest.mark.parametrize("study_id", STUDY_IDS)
def test_real_study_help_is_owned_by_the_study(study_id: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lab.cli", "research", "run", study_id, "--help"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert f"lab research run {study_id}" in result.stdout
    assert "--start" in result.stdout
    assert "--end" in result.stdout


def test_research_list_discovers_sorted_runnable_studies_without_importing_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "zeta_study")
    create_study_package(studies, "alpha_study")
    create_study_package(studies, "not_executable", runner=False)
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)

    assert cli.main(["research", "list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["alpha-study", "zeta-study"]


@pytest.mark.parametrize(
    ("study_id", "message"),
    [
        ("unknown-study", "unknown Study"),
        ("not_executable", "malformed Study ID"),
        ("../escape", "malformed Study ID"),
    ],
)
def test_research_run_rejects_unknown_or_malformed_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    study_id: str,
    message: str,
) -> None:
    studies = tmp_path / "studies"
    studies.mkdir()
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)

    assert cli.main(["research", "run", study_id]) == 2
    assert message in capsys.readouterr().err


def test_research_run_reports_a_non_executable_study(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "not_executable", runner=False)
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)

    assert cli.main(["research", "run", "not-executable"]) == 2
    assert "non-executable Study" in capsys.readouterr().err


def test_research_discovery_rejects_a_malformed_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    package = create_study_package(studies, "valid_study", runner=False)
    (package / "cli.py").mkdir()
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)

    assert cli.main(["research", "list"]) == 1
    assert "malformed Study" in capsys.readouterr().err


def test_research_discovery_rejects_a_package_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    real_package = create_study_package(tmp_path / "outside", "linked_study")
    studies.mkdir()
    try:
        (studies / "linked_study").symlink_to(real_package, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314:
            raise
        pytest.skip(f"symlink creation unavailable: {exc}")
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)

    assert cli.main(["research", "list"]) == 1
    assert "symlink" in capsys.readouterr().err


@pytest.mark.parametrize("exit_code", [0, 23])
def test_research_run_forwards_arguments_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_code: int,
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "example_study")
    monkeypatch.setattr(research, "RESEARCH_STUDIES", studies)
    invocation = patch_child(monkeypatch, exit_code)

    assert (
        cli.main(
            [
                "research",
                "run",
                "example-study",
                "--help",
                "--study-option",
                "value",
            ]
        )
        == exit_code
    )
    assert invocation == {
        "command": [
            sys.executable,
            "-m",
            "market_research.studies.example_study.cli",
            "--help",
            "--study-option",
            "value",
        ],
        "cwd": research.ROOT,
    }
