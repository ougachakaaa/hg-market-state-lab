"""Repository integration invariants surviving the Research architectural reset."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RETIRED = ("observations", "shared", "studies", "ui", "v2")


def production_sources() -> list[Path]:
    roots = [ROOT / "ui_cli"]
    for module in ("data_lake", "data_snapshot", "market_research", "ui_http"):
        roots.extend((ROOT / module).glob("**/src"))
    return sorted({p for root in roots for p in root.rglob("*.py") if "tests" not in p.parts})


def imports(source: Path) -> list[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return [
        name
        for node in ast.walk(tree)
        for name in (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module]
            if isinstance(node, ast.ImportFrom) and node.module is not None
            else []
        )
    ]


def test_no_production_imports_target_retired_research_packages() -> None:
    retired = tuple(f"market_research.{name}" for name in RETIRED)
    violations = [
        f"{source.relative_to(ROOT)} -> {name}"
        for source in production_sources()
        for name in imports(source)
        if any(name == prefix or name.startswith(prefix + ".") for prefix in retired)
    ]
    assert not violations, violations


def test_upstream_modules_have_no_reverse_research_dependency() -> None:
    violations = [
        f"{source.relative_to(ROOT)} -> {name}"
        for source in production_sources()
        if source.relative_to(ROOT).parts[0] in {"data_lake", "data_snapshot"}
        for name in imports(source)
        if name == "market_research" or name.startswith("market_research.")
    ]
    assert not violations, violations


def test_packaging_and_tooling_reference_existing_roots() -> None:
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    tool = manifest["tool"]
    for package in tool["poetry"]["packages"]:
        assert (ROOT / package.get("from", ".") / package["include"]).is_dir(), package
    paths = [
        *tool["pytest"]["ini_options"]["testpaths"],
        *tool["pytest"]["ini_options"]["pythonpath"],
        *tool["ruff"]["src"],
        *tool["mypy"]["files"],
        *tool["mypy"]["mypy_path"],
    ]
    for path in paths:
        assert (ROOT / path).is_dir(), path
        assert not any(path.startswith(f"market_research/{name}/") for name in RETIRED)
