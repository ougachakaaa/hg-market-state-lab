"""CLI consumption stays on the stable Dataset public API."""

import ast
from pathlib import Path


def test_lab_uses_only_dataset_public_boundaries() -> None:
    source = Path(__file__).resolve().parents[1]
    for path in source.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module]
                if isinstance(node, ast.ImportFrom) and node.module
                else []
            )
            for name in names:
                if name == "data_lake.datasets" and isinstance(node, ast.ImportFrom):
                    assert {alias.name for alias in node.names} <= {
                        "tushare_trade_calendar",
                        "tushare_index_daily",
                        "tushare_equity_index_futures",
                        "tushare_equity_index_options",
                    }
                if name.startswith("data_lake"):
                    assert name in {
                        "data_lake",
                        "data_lake.datasets",
                        "data_lake.datasets.tushare_trade_calendar",
                    }, path
