"""Only conversion may adapt to the Statistics root public sample contract."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/market_research"
CONVERSION = "market_research.descriptive.conversion"
OBSERVATION = "market_research.descriptive.observation"


def check_imports(text: str, package: str) -> None:
    conversion = package == CONVERSION or package.startswith(CONVERSION + ".")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ImportFrom):
            names = [resolve_name("." * node.level + (node.module or ""), package)]
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        else:
            continue
        for name in names:
            if name == "market_statistics" or name.startswith("market_statistics."):
                assert conversion and name == "market_statistics", name
                assert isinstance(node, ast.ImportFrom), "Import only the required public types"
                assert {alias.name for alias in node.names} <= {"NumericSample", "InvalidSample"}
            if conversion:
                assert (
                    name
                    in {
                        "dataclasses",
                        "datetime",
                        "math",
                        "types",
                        "market_statistics",
                        OBSERVATION,
                    }
                    or name == CONVERSION
                    or name.startswith(CONVERSION + ".")
                ), name
            else:
                assert name != CONVERSION and not name.startswith(CONVERSION + "."), name


def test_conversion_imports_only_public_contracts_and_has_no_effectful_dependencies() -> None:
    for path in SOURCE.rglob("*.py"):
        package = ".".join(("market_research", *path.relative_to(SOURCE).parent.parts))
        check_imports(path.read_text(encoding="utf-8"), package)
    assert not list(SOURCE.rglob("*executor*"))
    assert not list(SOURCE.rglob("*association*"))


@pytest.mark.parametrize(
    "text,package",
    [
        ("from market_statistics.models import NumericSample", CONVERSION),
        ("from market_statistics import compute", CONVERSION),
        ("import market_statistics", CONVERSION),
        ("from market_statistics import NumericSample", OBSERVATION),
        ("from ..conversion import convert", OBSERVATION),
        ("from market_research.descriptive.conversion import convert", OBSERVATION),
        ("from ..observation.models import ObservationSet", CONVERSION),
        ("from ..cases.trailing_return import prepare_inputs", CONVERSION),
        ("from data_lake.datasets.tushare_index_daily import create_service", CONVERSION),
        ("import socket", CONVERSION),
        ("import sqlite3", CONVERSION),
    ],
)
def test_boundary_check_rejects_extra_permissions(text: str, package: str) -> None:
    with pytest.raises(AssertionError):
        check_imports(text, package)
