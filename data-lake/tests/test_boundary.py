"""DataLake remains independent of consumer implementations and concrete Datasets."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data-lake/src/data_lake"


def test_core_has_no_cross_module_or_provider_dependencies() -> None:
    forbidden = {
        "market_snapshot",
        "market_research",
        "market_modeling",
        "backend_api",
        "lab",
        "tushare",
        "fastapi",
    }
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module]
                if isinstance(node, ast.ImportFrom) and node.module
                else []
            )
            assert not any(name.split(".")[0] in forbidden for name in names), path


def test_concrete_datasets_remain_authority_only() -> None:
    assert not list((ROOT / "data-lake/datasets").rglob("*.py"))
    assert not (SOURCE / "datasets").exists()


def test_no_consumer_imports_core_internals() -> None:
    for directory in ("lab", "backend-api/src", "market-snapshot/src", "market-research/src"):
        for path in (ROOT / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module]
                    if isinstance(node, ast.ImportFrom) and node.module
                    else []
                )
                assert not any(name.startswith("data_lake._") for name in names), path
