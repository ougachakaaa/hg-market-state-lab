"""Tests for the repository-level human/developer CLI."""

from __future__ import annotations

import ast
import importlib
import importlib.metadata
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPOSITORY_ROOT / "lab" / "cli.py"
STUDY_IDS = (
    "im-basis-baseline",
    "im-basis-forward-return-association",
    "price-to-lagged-ma-distribution",
)


lab = importlib.import_module("lab.cli")


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

    monkeypatch.setattr(lab.subprocess, "Popen", fake_popen)
    return invocation


def create_study_package(root: Path, package_name: str, *, runner: bool = True) -> Path:
    package = root / package_name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if runner:
        (package / "cli.py").write_text("", encoding="utf-8")
    return package


def test_root_and_research_help_are_layered(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        lab.main(["--help"])
    root_help = capsys.readouterr().out
    assert "{doctor,serve,research}" in root_help
    assert "research" in root_help

    with pytest.raises(SystemExit, match="0"):
        lab.main(["serve", "--help"])
    assert "{backend,frontend}" in capsys.readouterr().out
    assert "data" not in root_help

    with pytest.raises(SystemExit, match="0"):
        lab.main(["research", "--help"])
    research_help = capsys.readouterr().out
    assert "{list,run}" in research_help


@pytest.mark.parametrize("command", ["backend", "frontend"])
def test_old_flat_service_commands_are_not_exposed(command: str) -> None:
    with pytest.raises(SystemExit) as excinfo:
        lab.main([command])
    assert excinfo.value.code == 2


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
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)

    assert lab.main(["research", "list"]) == 0
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
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)

    assert lab.main(["research", "run", study_id]) == 2
    assert message in capsys.readouterr().err


def test_research_run_reports_a_non_executable_study(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "not_executable", runner=False)
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)

    assert lab.main(["research", "run", "not-executable"]) == 2
    assert "non-executable Study" in capsys.readouterr().err


def test_research_discovery_rejects_a_malformed_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    package = create_study_package(studies, "valid_study", runner=False)
    (package / "cli.py").mkdir()
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)

    assert lab.main(["research", "list"]) == 1
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
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)

    assert lab.main(["research", "list"]) == 1
    assert "symlink" in capsys.readouterr().err


@pytest.mark.parametrize("exit_code", [0, 23])
def test_research_run_forwards_arguments_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_code: int,
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "example_study")
    monkeypatch.setattr(lab, "RESEARCH_STUDIES", studies)
    invocation = patch_child(monkeypatch, exit_code)

    assert (
        lab.main(
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
        "cwd": lab.ROOT,
    }


@pytest.mark.parametrize("exit_code", [0, 23])
def test_backend_uses_the_backend_api_launcher(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    invocation = patch_child(monkeypatch, exit_code)

    assert lab.main(["serve", "backend"]) == exit_code
    assert invocation == {
        "command": [sys.executable, "backend-api/scripts/api.py"],
        "cwd": lab.ROOT,
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

    monkeypatch.setattr(lab.shutil, "which", lambda name: resolved_npm if name == "npm" else None)
    monkeypatch.setattr(lab.subprocess, "Popen", fake_popen)

    assert lab.main(["serve", "frontend"]) == exit_code
    assert invocation == {"command": [resolved_npm, "run", "dev"], "cwd": lab.FRONTEND}


@pytest.mark.parametrize("resolved_tool", ["/tools/npm", "C:/Tools/npm.cmd", "C:/Tools/npm.exe"])
def test_tool_version_uses_platform_resolved_executable(
    monkeypatch: pytest.MonkeyPatch, resolved_tool: str
) -> None:
    invocation: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        invocation["command"] = command
        invocation["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="test version", stderr="")

    monkeypatch.setattr(lab.shutil, "which", lambda name: resolved_tool if name == "npm" else None)
    monkeypatch.setattr(lab.subprocess, "run", fake_run)

    assert lab._tool_version("npm") == (resolved_tool, "test version")
    assert invocation["command"] == [resolved_tool, "--version"]
    assert "shell" not in invocation["kwargs"]


def test_data_command_is_retired() -> None:
    with pytest.raises(SystemExit) as excinfo:
        lab.main(["data"])
    assert excinfo.value.code == 2


def test_foreground_interrupt_reaps_child(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[int | None] = []

    class FakeChild:
        def wait(self, timeout: int | None = None) -> int:
            waits.append(timeout)
            if timeout is None:
                raise KeyboardInterrupt
            return 130

    monkeypatch.setattr(lab.subprocess, "Popen", lambda command, *, cwd: FakeChild())
    assert lab._run_foreground(["command"], lab.ROOT) == 130
    assert waits == [None, 2]


def test_doctor_inspects_current_root_python_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_tool_version(name: str) -> tuple[str, str]:
        return f"/tools/{name}", f"{name} test version"

    monkeypatch.setattr(lab, "_tool_version", fake_tool_version)
    monkeypatch.setattr(
        lab, "sys", SimpleNamespace(prefix=str(lab.ROOT / ".venv"), version_info=(3, 13, 15))
    )
    monkeypatch.setattr(lab, "_backend_status", lambda: "stopped")
    monkeypatch.setattr(lab, "_port_listening", lambda port: False)

    assert lab.doctor() == 0


def test_doctor_rejects_another_python_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(lab, "_tool_version", lambda name: (name, "test version"))
    monkeypatch.setattr(
        lab, "sys", SimpleNamespace(prefix=str(lab.ROOT / "other-venv"), version_info=(3, 13, 15))
    )
    monkeypatch.setattr(lab, "_backend_status", lambda: "stopped")
    monkeypatch.setattr(lab, "_port_listening", lambda port: False)

    assert lab.doctor() == 1
    assert "current Python is not root .venv" in capsys.readouterr().out


def test_repository_cli_does_not_import_owning_module_implementation() -> None:
    tree = ast.parse(CLI_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert not any(
        name.split(".", maxsplit=1)[0]
        in {"market_research", "market_snapshot", "backend_api"}
        for name in imported
    )


def test_root_cli_is_the_only_repository_executable_surface() -> None:
    manifest = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    scripts = manifest["project"].get("scripts", {})

    assert scripts == {"lab": "lab.cli:main"}
    assert manifest["tool"]["pytest"]["ini_options"]["testpaths"][0] == "lab/tests"
    assert not (REPOSITORY_ROOT / "tests").exists()
    installed_scripts = importlib.metadata.distribution("hg-market-state-lab").entry_points
    assert [(script.name, script.value) for script in installed_scripts] == [
        ("lab", "lab.cli:main")
    ]
    assert not (REPOSITORY_ROOT / "dev.py").exists()


@pytest.mark.parametrize("arguments", [["--help"], ["research", "list"]])
def test_installed_cli_runs_through_canonical_command(arguments: list[str]) -> None:
    poetry = shutil.which("poetry")
    assert poetry is not None
    result = subprocess.run(
        [poetry, "run", "lab", *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
