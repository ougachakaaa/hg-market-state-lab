"""Physical dependency checks for the HTTP ownership boundary."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SOURCE = REPOSITORY_ROOT / "ui_http/src/ui_http"
MARKET_SOURCE = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot"


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
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


def test_repository_owns_one_python_project_and_lockfile() -> None:
    manifests = sorted(
        path.relative_to(REPOSITORY_ROOT)
        for path in REPOSITORY_ROOT.rglob("pyproject.toml")
        if ".venv" not in path.parts
        and "node_modules" not in path.parts
        and "_temp_docs" not in path.parts
    )
    lockfiles = sorted(
        path.relative_to(REPOSITORY_ROOT)
        for path in REPOSITORY_ROOT.rglob("poetry.lock")
        if ".venv" not in path.parts
        and "node_modules" not in path.parts
        and "_temp_docs" not in path.parts
    )

    assert manifests == [Path("pyproject.toml")]
    assert lockfiles == [Path("poetry.lock")]


def test_root_project_installs_the_independent_package_namespaces() -> None:
    manifest = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert manifest["tool"]["poetry"]["packages"] == [
        {"include": "ui_cli"},
        {"include": "data_lake", "from": "data_lake/src"},
        {"include": "data_lake", "from": "data_lake/providers/tushare/src"},
        {"include": "data_lake", "from": "data_lake/datasets/tushare_trade_calendar/src"},
        {"include": "data_lake", "from": "data_lake/datasets/tushare_index_daily/src"},
        {"include": "data_lake", "from": "data_lake/datasets/tushare_equity_index_futures/src"},
        {"include": "data_lake", "from": "data_lake/datasets/tushare_equity_index_options/src"},
        {"include": "data_snapshot", "from": "data_snapshot/src"},
        {"include": "market_research", "from": "market_research/src"},
        {"include": "market_statistics", "from": "market_statistics/src"},
        {"include": "ui_http", "from": "ui_http/src"},
    ]
    assert not any(
        "path" in dependency or "develop" in dependency
        for dependency in manifest["project"]["dependencies"]
    )


def test_repository_poetry_config_requires_a_root_local_environment() -> None:
    config = tomllib.loads(
        (REPOSITORY_ROOT / "poetry.toml").read_text(encoding="utf-8")
    )

    assert config["virtualenvs"]["in-project"] is True


def test_backend_uses_only_public_product_service_boundaries() -> None:
    allowed = {
        "data_snapshot.products.mo_option_chain",
        "data_snapshot.products.mo_option_chain.service",
        "data_snapshot.products.mo_option_premium",
        "data_snapshot.products.mo_option_premium.service",
    }
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for source in BACKEND_SOURCE.rglob("*.py")
        for name in imported_modules(source)
        if name.startswith("data_snapshot") and name not in allowed
    ]

    assert not violations, "non-public data_snapshot imports:\n" + "\n".join(violations)


def test_market_snapshot_has_no_reverse_backend_dependency() -> None:
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for source in MARKET_SOURCE.rglob("*.py")
        for name in imported_modules(source)
        if name == "ui_http" or name.startswith("ui_http.")
    ]

    assert not violations, "reverse backend imports:\n" + "\n".join(violations)


def test_market_snapshot_contains_no_fastapi_runtime_package() -> None:
    assert not (MARKET_SOURCE / "api").exists()
    assert not (REPOSITORY_ROOT / "data_snapshot/scripts/api.py").exists()


def test_research_transport_uses_only_admitted_public_boundaries() -> None:
    allowed = {
        "market_research.descriptive.capabilities", "market_research.descriptive.execution",
        "market_research.descriptive.association", "market_research.descriptive.observation",
        "market_research.descriptive.cases.trailing_return", "market_statistics",
    }
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for source in BACKEND_SOURCE.rglob("*.py")
        for name in imported_modules(source)
        if (name.startswith(("market_research", "market_statistics", "data_lake")))
        and name not in allowed
    ]
    assert not violations, violations


def test_research_and_statistics_have_no_reverse_http_dependency() -> None:
    forbidden = ("ui_http", "fastapi", "starlette", "uvicorn")
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for module in ("market_research", "market_statistics")
        for source in (REPOSITORY_ROOT / module / "src").rglob("*.py")
        for name in imported_modules(source)
        if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
    ]
    assert not violations, violations
