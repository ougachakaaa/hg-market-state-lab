"""Repository configuration and Python environment boundaries."""

from __future__ import annotations

import ast
import subprocess
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_SOURCE = REPO_ROOT / "config/src/lab_config/__init__.py"
SKIP_PARTS = frozenset({".venv", "node_modules", "_temp_docs", "__pycache__"})
BUSINESS_PACKAGES = frozenset(
    {
        "data_lake",
        "data_snapshot",
        "market_research",
        "market_statistics",
        "ui_cli",
        "ui_http",
        "workbench",
    }
)


def production_sources() -> list[Path]:
    roots = [
        REPO_ROOT / "data_lake/src",
        *sorted((REPO_ROOT / "data_lake/providers").glob("*/src")),
        *sorted((REPO_ROOT / "data_lake/datasets").glob("*/src")),
        REPO_ROOT / "data_lake/experiments",
        REPO_ROOT / "data_snapshot/src",
        REPO_ROOT / "market_research/src",
        REPO_ROOT / "market_research/scripts",
        REPO_ROOT / "market_statistics/src",
        REPO_ROOT / "ui_http/src",
        REPO_ROOT / "ui_cli",
        REPO_ROOT / "workbench",
        REPO_ROOT / "ui_web/scripts",
    ]
    return [root for root in roots if root.exists()]


def python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if SKIP_PARTS.intersection(path.parts):
            continue
        if "tests" in path.parts or path.name.startswith("test_"):
            continue
        yield path


def imported_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
                names.extend(f"{node.module}.{alias.name}" for alias in node.names)
            if node.module == "os":
                names.extend(alias.name for alias in node.names)
    return names


def direct_environment_reads(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    reads: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
            and node.attr in {"environ", "getenv"}
        ):
            reads.append(f"os.{node.attr}")
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            reads.extend(
                f"os.{alias.name}"
                for alias in node.names
                if alias.name in {"environ", "getenv"}
            )
    return reads


def test_lab_config_does_not_depend_on_business_modules() -> None:
    imported = imported_names(CONFIG_SOURCE)
    assert not any(name.split(".")[0] in BUSINESS_PACKAGES for name in imported)


def test_production_sources_route_environment_reads_through_lab_config() -> None:
    violations: list[str] = []
    for root in production_sources():
        for path in python_files(root):
            imported = imported_names(path)
            if any(
                name == "dotenv"
                or name.startswith("dotenv.")
                or name == "pydantic_settings"
                or name.startswith("pydantic_settings.")
                for name in imported
            ):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports a settings loader")
            reads = direct_environment_reads(path)
            if reads:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} reads {'/'.join(sorted(set(reads)))}"
                )
    assert not violations, "direct environment configuration reads:\n" + "\n".join(violations)


def test_only_the_root_owns_a_python_virtual_environment() -> None:
    nested = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.iterdir()
        if path.is_dir()
        and path.name not in {".venv", ".git"}
        and (path / ".venv").exists()
    ]
    assert not nested, "module-local Python environments:\n" + "\n".join(nested)


def test_local_configuration_is_ignored_and_the_template_is_tracked() -> None:
    local = [
        subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", "--", path],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
        for path in (
            ".env",
            "data_snapshot/.env",
            "config/.env",
            "ui_http/.env",
            "market_research/.env",
            "arbitrary/deep/directory/.env",
        )
    ]
    template = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", ".env.example"],
        cwd=REPO_ROOT,
        check=False,
    )

    assert all(code == 0 for code in local)
    assert template.returncode == 1

    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.split("\0")
    assert ".env.example" in tracked
    assert not any(Path(path).name == ".env" for path in tracked)
