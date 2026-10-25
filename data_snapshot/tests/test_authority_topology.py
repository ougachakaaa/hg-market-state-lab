"""Repository-wide checks for co-located authority and progressive disclosure."""

from __future__ import annotations

import ast
import re
from collections import deque
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")

CONTEXT_ENTRIES = {
    Path("market_research/ARCHITECTURE.md"),
    Path("market_research/UPSTREAM.md"),
    Path("market_research/descriptive/ARCHITECTURE.md"),
    Path("data_lake/EXPERIMENTS.md"),
    Path("data_lake/DIAGNOSTICS.md"),
    Path("data_lake/datasets/tushare_equity_index_options/CONTRACT_UNIVERSE.md"),
    Path("data_lake/datasets/tushare_equity_index_options/TRADING_DAYS.md"),
    Path("data_lake/datasets/tushare_equity_index_options/FACTS.md"),
    Path("data_lake/datasets/tushare_equity_index_options/SERVICE.md"),
    Path("data_lake/datasets/tushare_equity_index_options/ARCHITECTURE.md"),
    Path("data_lake/datasets/tushare_equity_index_futures/CONTRACT_UNIVERSE.md"),
    Path("data_lake/datasets/tushare_equity_index_futures/TRADING_DAYS.md"),
    Path("data_lake/datasets/tushare_equity_index_futures/FACTS.md"),
    Path("data_lake/datasets/tushare_equity_index_futures/SERVICE.md"),
    Path("data_lake/datasets/tushare_equity_index_futures/ARCHITECTURE.md"),
    Path("data_lake/datasets/tushare_index_daily/TRADING_DAYS.md"),
    Path("data_lake/datasets/tushare_index_daily/FACTS.md"),
    Path("data_lake/datasets/tushare_index_daily/SERVICE.md"),
    Path("data_lake/datasets/tushare_index_daily/ARCHITECTURE.md"),
    Path("data_lake/providers/tushare/ARCHITECTURE.md"),
    Path("data_lake/ARCHITECTURE.md"),
    Path("data_lake/EXECUTION.md"),
    Path("data_lake/PERSISTENCE.md"),
    Path("data_lake/DOMAIN_MODEL.md"),
    Path("data_lake/APPLICATION.md"),
    Path("data_lake/DATASETS.md"),
    Path("data_lake/datasets/tushare_trade_calendar/ARCHITECTURE.md"),
    Path("data_lake/datasets/tushare_trade_calendar/SERVICE.md"),
    Path("data_snapshot/src/data_snapshot/capture/ARCHITECTURE.md"),
    Path(
        "data_snapshot/src/data_snapshot/products/"
        "daily_market_snapshot/ARCHITECTURE.md"
    ),
    Path("data_snapshot/src/data_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md"),
    Path("data_snapshot/src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md"),
    Path(
        "data_snapshot/src/data_snapshot/products/"
        "cffex_equity_index_basis_history/ARCHITECTURE.md"
    ),
    Path("data_snapshot/src/data_snapshot/products/index_daily_history/ARCHITECTURE.md"),
    Path(
        "data_snapshot/src/data_snapshot/products/"
        "mo_option_chain/ARCHITECTURE.md"
    ),
    Path(
        "data_snapshot/src/data_snapshot/products/"
        "mo_option_premium/ARCHITECTURE.md"
    ),
    Path("ui_web/src/features/mo_option_chain/ARCHITECTURE.md"),
}


def authority_markdown() -> list[Path]:
    return [
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if "_temp_docs" not in path.parts
        and "node_modules" not in path.parts
        and ".venv" not in path.parts
    ]


def local_markdown_targets(path: Path) -> list[Path]:
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if resolved.suffix.lower() == ".md":
            targets.append(resolved)
    return targets


def test_all_local_markdown_links_resolve() -> None:
    broken = [
        f"{path.relative_to(REPOSITORY_ROOT)} -> {target}"
        for path in authority_markdown()
        for target in local_markdown_targets(path)
        if not target.is_file()
    ]
    assert not broken, "broken authority links:\n" + "\n".join(broken)


def test_context_authority_is_reachable_from_the_root_entry() -> None:
    root_entry = (REPOSITORY_ROOT / "ARCHITECTURE.md").resolve()
    pending = deque([root_entry])
    visited: set[Path] = set()
    while pending:
        current = pending.popleft()
        if current in visited or not current.is_file():
            continue
        visited.add(current)
        pending.extend(local_markdown_targets(current))

    missing = {
        path for path in CONTEXT_ENTRIES if (REPOSITORY_ROOT / path).resolve() not in visited
    }
    assert not missing, f"context authority is unreachable: {sorted(map(str, missing))}"


def test_retired_snapshot_implementation_is_absent() -> None:
    snapshot_root = REPOSITORY_ROOT / "data_snapshot"
    package_root = snapshot_root / "src/data_snapshot"
    retired_paths = (
        snapshot_root / "scripts/dms.py",
        package_root / "cli.py",
        snapshot_root / "output/.gitkeep",
    )
    assert not any(path.exists() for path in retired_paths)
    assert not list((package_root / "services").glob("*.py"))
    assert not list((package_root / "products/csi1000_5d_analysis").glob("*.py"))


def test_cffex_basis_semantics_have_one_shared_implementation() -> None:
    package_root = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot"
    product_root = package_root / "products/csi1000_im_basis_history"
    assert (package_root / "cffex_equity_index_basis/semantics.py").is_file()
    assert (product_root / "basis_semantics.py").is_file()
    compatibility_source = (product_root / "basis_semantics.py").read_text(encoding="utf-8")
    assert "from ...cffex_equity_index_basis.semantics import" in compatibility_source
    assert "def assign_contract_slots" not in compatibility_source
    assert not (package_root / "preparation/im_basis").exists()
    for source in product_root.glob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and "preparation.im_basis" in node.module
            for node in ast.walk(tree)
        ), source


def test_shared_artifacts_do_not_define_product_raw_paths() -> None:
    source = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot/artifacts.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    product_path_names = {
        "daily_raw_dir",
        "mo_option_chain_raw_dir",
        "mo_option_premium_raw_dir",
        "MO_OPTION_CHAIN_RAW_SUBDIR",
        "MO_OPTION_PREMIUM_RAW_SUBDIR",
    }
    defined_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    } | {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert not product_path_names & defined_names


def test_central_guides_do_not_return() -> None:
    forbidden_directories = (
        REPOSITORY_ROOT / "data_snapshot/guides",
        REPOSITORY_ROOT / "ui_web/guides",
    )
    assert not any(path.exists() for path in forbidden_directories)

    text_suffixes = {".md", ".py", ".toml", ".json", ".ts", ".tsx"}
    obsolete_fragment = "guides" + "/"
    offenders = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path in REPOSITORY_ROOT.rglob("*")
        if path.is_file()
        and "_temp_docs" not in path.parts
        and "node_modules" not in path.parts
        and ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix in text_suffixes
        and obsolete_fragment in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, f"obsolete guides references: {offenders}"


def test_capability_catalog_is_navigation_only() -> None:
    catalog = (REPOSITORY_ROOT / "data_snapshot/CAPABILITIES.md").read_text(
        encoding="utf-8"
    )
    assert len(catalog.splitlines()) < 80
    for forbidden_heading in ("## Fields", "## Formula", "## DTO", "## Failure semantics"):
        assert forbidden_heading not in catalog


def test_product_packages_do_not_import_sibling_products() -> None:
    products_root = (
        REPOSITORY_ROOT / "data_snapshot/src/data_snapshot/products"
    )
    violations: list[str] = []
    for product in products_root.iterdir():
        if not product.is_dir():
            continue
        sibling_names = {
            sibling.name
            for sibling in products_root.iterdir()
            if sibling.is_dir() and sibling != product
        }
        for source in product.rglob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            imported_modules = [
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
            for sibling in sibling_names:
                absolute = f"data_snapshot.products.{sibling}"
                if any(
                    imported == sibling
                    or imported.startswith(f"{sibling}.")
                    or imported == absolute
                    or imported.startswith(f"{absolute}.")
                    for imported in imported_modules
                ):
                    violations.append(f"{source.relative_to(REPOSITORY_ROOT)} -> {sibling}")
    assert not violations, "sibling product imports:\n" + "\n".join(violations)


def test_shared_capture_does_not_import_product_contexts() -> None:
    capture_root = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot/capture"
    offenders = [
        str(source.relative_to(REPOSITORY_ROOT))
        for source in capture_root.glob("*.py")
        if "data_snapshot.products" in source.read_text(encoding="utf-8")
        or "..products" in source.read_text(encoding="utf-8")
    ]
    assert not offenders, f"shared Capture imports product contexts: {offenders}"


def test_canonical_python_namespace_replaces_the_legacy_namespace() -> None:
    source_root = REPOSITORY_ROOT / "data_snapshot/src"

    assert (source_root / "data_snapshot/__init__.py").is_file()
    assert not (source_root / "daily_market_snapshot").exists()

    offenders: list[str] = []
    for root in (REPOSITORY_ROOT / "data_snapshot", REPOSITORY_ROOT / "ui_http"):
        for path in root.rglob("*.py"):
            if ".venv" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = [
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
            if any(
                name == "daily_market_snapshot"
                or name.startswith("daily_market_snapshot.")
                for name in imported
            ):
                offenders.append(str(path.relative_to(REPOSITORY_ROOT)))
    assert not offenders, f"legacy namespace references: {offenders}"


def test_market_snapshot_production_owns_no_http_runtime() -> None:
    source_root = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot"
    forbidden = ("fastapi", "starlette", "uvicorn", "ui_http")
    offenders: list[str] = []
    for source in source_root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        imported = [
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
        if any(name.startswith(forbidden) for name in imported):
            offenders.append(str(source.relative_to(REPOSITORY_ROOT)))

    assert not offenders, f"HTTP runtime imports in data_snapshot: {offenders}"


def test_market_snapshot_does_not_depend_on_market_research() -> None:
    source_root = REPOSITORY_ROOT / "data_snapshot/src/data_snapshot"
    offenders = [
        str(source.relative_to(REPOSITORY_ROOT))
        for source in source_root.rglob("*.py")
        if "market_research" in source.read_text(encoding="utf-8")
    ]
    assert not offenders, f"data_snapshot imports market_research: {offenders}"
