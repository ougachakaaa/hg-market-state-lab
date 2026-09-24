"""Repository-wide checks for co-located authority and progressive disclosure."""

from __future__ import annotations

import ast
import re
from collections import deque
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")

CONTEXT_ENTRIES = {
    Path("market-snapshot/src/daily_market_snapshot/capture/ARCHITECTURE.md"),
    Path("market-snapshot/src/daily_market_snapshot/services/ARCHITECTURE.md"),
    Path(
        "market-snapshot/src/daily_market_snapshot/products/"
        "daily_market_snapshot/ARCHITECTURE.md"
    ),
    Path(
        "market-snapshot/src/daily_market_snapshot/products/"
        "csi1000_5d_analysis/ARCHITECTURE.md"
    ),
    Path(
        "market-snapshot/src/daily_market_snapshot/products/"
        "mo_option_chain/ARCHITECTURE.md"
    ),
    Path(
        "market-snapshot/src/daily_market_snapshot/products/"
        "mo_option_premium/ARCHITECTURE.md"
    ),
    Path("web-ui/src/features/mo_option_chain/ARCHITECTURE.md"),
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


def test_central_guides_do_not_return() -> None:
    forbidden_directories = (
        REPOSITORY_ROOT / "market-snapshot/guides",
        REPOSITORY_ROOT / "web-ui/guides",
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
        and "__pycache__" not in path.parts
        and path.suffix in text_suffixes
        and obsolete_fragment in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, f"obsolete guides references: {offenders}"


def test_capability_catalog_is_navigation_only() -> None:
    catalog = (REPOSITORY_ROOT / "market-snapshot/CAPABILITIES.md").read_text(
        encoding="utf-8"
    )
    assert len(catalog.splitlines()) < 80
    for forbidden_heading in ("## Fields", "## Formula", "## DTO", "## Failure semantics"):
        assert forbidden_heading not in catalog


def test_product_packages_do_not_import_sibling_products() -> None:
    products_root = (
        REPOSITORY_ROOT / "market-snapshot/src/daily_market_snapshot/products"
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
                absolute = f"daily_market_snapshot.products.{sibling}"
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
    capture_root = REPOSITORY_ROOT / "market-snapshot/src/daily_market_snapshot/capture"
    offenders = [
        str(source.relative_to(REPOSITORY_ROOT))
        for source in capture_root.glob("*.py")
        if "daily_market_snapshot.products" in source.read_text(encoding="utf-8")
        or "..products" in source.read_text(encoding="utf-8")
    ]
    assert not offenders, f"shared Capture imports product contexts: {offenders}"
