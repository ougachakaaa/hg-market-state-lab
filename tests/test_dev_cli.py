"""Tests for the repository-level human/developer CLI."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEV_PATH = REPOSITORY_ROOT / "dev.py"
POETRY = str(REPOSITORY_ROOT / "tools" / "poetry")
NPM = "/tools/npm"
STUDY_IDS = (
    "im-basis-baseline",
    "im-basis-forward-return-association",
    "price-to-lagged-ma-distribution",
)


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


def create_study_package(root: Path, package_name: str, *, runner: bool = True) -> Path:
    package = root / package_name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if runner:
        (package / "cli.py").write_text("", encoding="utf-8")
    return package


def test_root_and_research_help_are_layered(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        dev.main(["--help"])
    root_help = capsys.readouterr().out
    assert all(command in root_help for command in ("doctor", "backend", "frontend"))
    assert "research" in root_help
    assert "data" not in root_help

    with pytest.raises(SystemExit, match="0"):
        dev.main(["research", "--help"])
    research_help = capsys.readouterr().out
    assert "{list,run}" in research_help


@pytest.mark.parametrize("study_id", STUDY_IDS)
def test_real_study_help_is_owned_by_the_study(study_id: str) -> None:
    result = subprocess.run(
        [sys.executable, str(DEV_PATH), "research", "run", study_id, "--help"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert f"dev.py research run {study_id}" in result.stdout
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
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)

    assert dev.main(["research", "list"]) == 0
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
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)

    assert dev.main(["research", "run", study_id]) == 2
    assert message in capsys.readouterr().err


def test_research_run_reports_a_non_executable_study(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "not_executable", runner=False)
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)

    assert dev.main(["research", "run", "not-executable"]) == 2
    assert "non-executable Study" in capsys.readouterr().err


def test_research_discovery_rejects_a_malformed_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    studies = tmp_path / "studies"
    package = create_study_package(studies, "valid_study", runner=False)
    (package / "cli.py").mkdir()
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)

    assert dev.main(["research", "list"]) == 1
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
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)

    assert dev.main(["research", "list"]) == 1
    assert "symlink" in capsys.readouterr().err


@pytest.mark.parametrize("exit_code", [0, 23])
def test_research_run_forwards_arguments_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_code: int,
) -> None:
    studies = tmp_path / "studies"
    create_study_package(studies, "example_study")
    monkeypatch.setattr(dev, "RESEARCH_STUDIES", studies)
    invocation = patch_child(monkeypatch, exit_code)

    assert (
        dev.main(
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
        "cwd": dev.ROOT,
    }


def test_backend_uses_the_backend_api_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    invocation = patch_child(monkeypatch, 0)

    assert dev.main(["backend"]) == 0
    assert invocation == {
        "command": [POETRY, "run", "python", "backend-api/scripts/api.py"],
        "cwd": dev.ROOT,
    }


def test_frontend_uses_the_web_ui_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    invocation: dict[str, Any] = {}

    class FakeChild:
        def wait(self, timeout: int | None = None) -> int:
            assert timeout is None
            return 0

    def fake_popen(command: list[str], *, cwd: Path) -> FakeChild:
        invocation["command"] = command
        invocation["cwd"] = cwd
        return FakeChild()

    monkeypatch.setattr(dev.shutil, "which", lambda name: NPM if name == "npm" else None)
    monkeypatch.setattr(dev.subprocess, "Popen", fake_popen)

    assert dev.main(["frontend"]) == 0
    assert invocation == {"command": [NPM, "run", "dev"], "cwd": dev.FRONTEND}


def test_data_command_is_retired() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev.main(["data"])
    assert excinfo.value.code == 2


def test_doctor_inspects_one_root_poetry_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poetry_calls: list[str] = []

    def fake_tool_version(name: str) -> tuple[str, str]:
        return f"/tools/{name}", f"{name} test version"

    def fake_poetry_python(poetry: str) -> tuple[Path, str]:
        poetry_calls.append(poetry)
        return dev.ROOT / ".venv/bin/python", "3.13.15"

    monkeypatch.setattr(dev, "_tool_version", fake_tool_version)
    monkeypatch.setattr(dev, "_poetry_python", fake_poetry_python)
    monkeypatch.setattr(dev, "_backend_status", lambda: "stopped")
    monkeypatch.setattr(dev, "_port_listening", lambda port: False)

    assert dev.doctor() == 0
    assert poetry_calls == ["/tools/poetry"]


def test_repository_cli_does_not_import_research_implementation() -> None:
    tree = ast.parse(DEV_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert not any(
        name == "market_research" or name.startswith("market_research.")
        for name in imported
    )


def test_root_cli_is_the_only_research_executable_surface() -> None:
    manifest = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    scripts = manifest["project"].get("scripts", {})

    assert "market-research" not in scripts
    assert scripts.get("market-research") != "market_research.ui.cli:main"
    assert not any(
        entry_point.split(":", maxsplit=1)[0] == "market_research"
        or entry_point.split(":", maxsplit=1)[0].startswith("market_research.")
        for entry_point in scripts.values()
    )
