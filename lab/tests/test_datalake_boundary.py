"""CLI consumption stays on the stable Dataset public API."""

import ast
from pathlib import Path


def test_lab_uses_only_calendar_public_boundary() -> None:
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
                if name.startswith("data_lake"):
                    assert name in {"data_lake", "data_lake.datasets.tushare_trade_calendar"}, path
