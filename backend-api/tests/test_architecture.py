"""Physical dependency checks for the HTTP ownership boundary."""

from __future__ import annotations

import ast
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


def test_backend_declares_market_snapshot_as_a_path_dependency() -> None:
    manifest = (REPOSITORY_ROOT / "backend-api/pyproject.toml").read_text(encoding="utf-8")

    assert 'market-snapshot = { path = "../market-snapshot", develop = true }' in manifest


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
