"""Conversion and association consume precise, distinct public Statistics contracts."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/market_research"
CONVERSION = "market_research.descriptive.conversion"
OBSERVATION = "market_research.descriptive.observation"
ASSOCIATION = "market_research.descriptive.association"
ASSOCIATION_STATISTICS = {
    "NumericSample",
    "InvalidSample",
    "InvalidStatisticalSpec",
    "StatisticalSpec",
    "StatisticalResult",
    "QuantileSpec",
    "QuantileResult",
    "IntervalCountSpec",
    "IntervalCountResult",
    "IntervalBin",
    "validate_spec",
}


def check_imports(text: str, package: str) -> None:
    conversion = package == CONVERSION or package.startswith(CONVERSION + ".")
    association = package == ASSOCIATION or package.startswith(ASSOCIATION + ".")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ImportFrom):
            names = [resolve_name("." * node.level + (node.module or ""), package)]
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        else:
            continue
        for name in names:
            if name == "market_statistics" or name.startswith("market_statistics."):
                assert (conversion or association) and name == "market_statistics", name
                assert isinstance(node, ast.ImportFrom), "Import only the required public types"
                allowed = (
                    ASSOCIATION_STATISTICS if association else {"NumericSample", "InvalidSample"}
                )
                assert {alias.name for alias in node.names} <= allowed
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
            elif association:
                assert (
                    name
                    in {
                        "dataclasses",
                        "datetime",
                        "math",
                        "types",
                        "market_statistics",
                        OBSERVATION,
                        CONVERSION,
                    }
                    or name == ASSOCIATION
                    or name.startswith(ASSOCIATION + ".")
                ), name
                if name == CONVERSION:
                    assert isinstance(node, ast.ImportFrom)
                    assert {alias.name for alias in node.names} <= {
                        "SampleBinding",
                        "SampleProjection",
                    }
            else:
                assert name != CONVERSION and not name.startswith(CONVERSION + "."), name
            if not association:
                assert name != ASSOCIATION and not name.startswith(ASSOCIATION + "."), name


def test_conversion_imports_only_public_contracts_and_has_no_effectful_dependencies() -> None:
    for path in SOURCE.rglob("*.py"):
        package = ".".join(("market_research", *path.relative_to(SOURCE).parent.parts))
        check_imports(path.read_text(encoding="utf-8"), package)
    assert not list(SOURCE.rglob("*executor*"))


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
        ("from market_statistics.models import QuantileResult", ASSOCIATION),
        ("from market_statistics import compute", ASSOCIATION),
        ("import market_statistics", ASSOCIATION),
        ("from ..conversion import convert", ASSOCIATION),
        ("from ..conversion.validation import validate_source", ASSOCIATION),
        ("from ..observation.models import ObservationSet", ASSOCIATION),
        ("from ..cases.trailing_return import prepare_inputs", ASSOCIATION),
        ("from ..execution import execute_job", ASSOCIATION),
        ("from data_lake.datasets.tushare_index_daily import create_service", ASSOCIATION),
        ("from data_snapshot import capture", ASSOCIATION),
        ("import socket", ASSOCIATION),
        ("import pathlib", ASSOCIATION),
        ("import sqlite3", ASSOCIATION),
        ("import random", ASSOCIATION),
        ("import time", ASSOCIATION),
        ("from ..association import associate", CONVERSION),
        ("from ..association import associate", OBSERVATION),
    ],
)
def test_boundary_check_rejects_extra_permissions(text: str, package: str) -> None:
    with pytest.raises(AssertionError):
        check_imports(text, package)
