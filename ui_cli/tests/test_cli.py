"""Command topology, installation, and architecture checks."""

from __future__ import annotations

import ast
import importlib.metadata
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from ui_cli import cli

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPOSITORY_ROOT / "ui_cli" / "cli.py"


def test_root_and_service_help_are_layered(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        cli.main(["--help"])
    root_help = capsys.readouterr().out
    assert "{doctor,serve,datalake}" in root_help
    assert "research" not in root_help

    with pytest.raises(SystemExit, match="0"):
        cli.main(["serve", "--help"])
    assert "{backend,frontend}" in capsys.readouterr().out
    assert "datalake" in root_help


@pytest.mark.parametrize("command", ["backend", "frontend"])
def test_old_flat_service_commands_are_not_exposed(command: str) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main([command])
    assert excinfo.value.code == 2


def test_data_command_is_retired() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["data"])
    assert excinfo.value.code == 2


def test_repository_cli_does_not_import_owning_module_implementation() -> None:
    imported: list[str] = []
    for source in (REPOSITORY_ROOT / "ui_cli").glob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
    assert not any(
        name.split(".", maxsplit=1)[0]
        in {"market_research", "data_snapshot", "ui_http"}
        for name in imported
    )


def test_root_cli_is_the_only_repository_executable_surface() -> None:
    manifest = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    scripts = manifest["project"].get("scripts", {})

    assert scripts == {"lab": "ui_cli.cli:main"}
    assert manifest["tool"]["pytest"]["ini_options"]["testpaths"][0] == "ui_cli/tests"
    assert not (REPOSITORY_ROOT / "tests").exists()
    installed_scripts = importlib.metadata.distribution("hg-market-state-lab").entry_points
    assert [(script.name, script.value) for script in installed_scripts] == [
        ("lab", "ui_cli.cli:main")
    ]
    assert not (REPOSITORY_ROOT / "dev.py").exists()


@pytest.mark.parametrize("arguments", [["--help"], ["datalake", "list"]])
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
    if arguments == ["--help"]:
        assert result.stdout.strip()
    else:
        assert "tushare_index_daily" in result.stdout.splitlines()


@pytest.mark.parametrize(
    "arguments",
    [["research", "list"], ["research", "run", "old-study"], ["research", "--help"]],
)
def test_retired_research_commands_are_rejected(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(arguments)
    assert excinfo.value.code == 2
