"""Physical dependency checks for the HTTP ownership boundary."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SOURCE = REPOSITORY_ROOT / "backend-api/src/backend_api"
MARKET_SOURCE = REPOSITORY_ROOT / "market-snapshot/src/market_snapshot"


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
        {"include": "lab"},
        {"include": "data_lake", "from": "data-lake/src"},
        {"include": "data_lake", "from": "data-lake/datasets/tushare_trade_calendar/src"},
        {"include": "data_lake", "from": "data-lake/datasets/tushare_index_daily/src"},
        {"include": "data_lake", "from": "data-lake/datasets/tushare_equity_index_futures/src"},
        {"include": "data_lake", "from": "data-lake/datasets/tushare_equity_index_options/src"},
        {"include": "market_snapshot", "from": "market-snapshot/src"},
        {"include": "backend_api", "from": "backend-api/src"},
        {
            "include": "market_research",
            "from": "market-research/observations/cffex_option_expiry_dte_chain/src",
        },
        {"include": "market_research", "from": "market-research/observations/src"},
        {
            "include": "market_research",
            "from": "market-research/shared/cffex_option_expiry_universe/src",
        },
        {"include": "market_research", "from": "market-research/shared/distribution/src"},
        {"include": "market_research", "from": "market-research/shared/im_basis/src"},
        {
            "include": "market_research",
            "from": "market-research/shared/price_to_lagged_reference/src",
        },
        {
            "include": "market_research",
            "from": "market-research/studies/cffex_option_expiry_dte_collection/src",
        },
        {"include": "market_research", "from": "market-research/ui/src"},
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
        "market_snapshot.products.mo_option_chain",
        "market_snapshot.products.mo_option_chain.service",
        "market_snapshot.products.mo_option_premium",
        "market_snapshot.products.mo_option_premium.service",
    }
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for source in BACKEND_SOURCE.rglob("*.py")
        for name in imported_modules(source)
        if name.startswith("market_snapshot") and name not in allowed
    ]

    assert not violations, "non-public market-snapshot imports:\n" + "\n".join(violations)


def test_market_snapshot_has_no_reverse_backend_dependency() -> None:
    violations = [
        f"{source.relative_to(REPOSITORY_ROOT)} -> {name}"
        for source in MARKET_SOURCE.rglob("*.py")
        for name in imported_modules(source)
        if name == "backend_api" or name.startswith("backend_api.")
    ]

    assert not violations, "reverse backend imports:\n" + "\n".join(violations)


def test_market_snapshot_contains_no_fastapi_runtime_package() -> None:
    assert not (MARKET_SOURCE / "api").exists()
    assert not (REPOSITORY_ROOT / "market-snapshot/scripts/api.py").exists()
