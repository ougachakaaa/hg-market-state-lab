"""Conversion and association consume precise, distinct public Statistics contracts."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/market_research"
CONVERSION = "market_research.descriptive.conversion"
OBSERVATION = "market_research.descriptive.observation"
ASSOCIATION = "market_research.descriptive.association"
EXECUTION = "market_research.descriptive.execution"
CASE = "market_research.descriptive.cases.trailing_return"
EXECUTION_PUBLIC = {
    OBSERVATION: {
        "DateWindow",
        "JobIdentity",
        "ObservationJobSpec",
        "ObservationSet",
        "ObservationConstructionFailure",
    },
    CONVERSION: {
        "SampleProjection",
        "InvalidObservationSet",
        "NoEligibleObservations",
        "UnmappableSample",
        "convert",
    },
    ASSOCIATION: {
        "AnalysisRequest",
        "ResearchAnalysisEvidence",
        "ResultAssociationFailure",
        "associate",
    },
    CASE: {
        "DEFINITION",
        "InputAttempt",
        "InputPreparationFailure",
        "PreparedInputs",
        "TrailingReturnProvenance",
        "prepare_inputs",
        "construct_observations",
        "validate_job",
    },
    "market_statistics": {
        "StatisticalResult",
        "StatisticalSpec",
        "IntervalCountSpec",
        "InvalidSample",
        "InvalidStatisticalSpec",
        "CalculationFailure",
        "validate_spec",
        "compute",
    },
}
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


def check_imports(
    text: str,
    package: str,
    *,
    publication: bool = False,
    basis_statistics: bool = False,
    basis_delivery: bool = False,
) -> None:
    conversion = package == CONVERSION or package.startswith(CONVERSION + ".")
    association = package == ASSOCIATION or package.startswith(ASSOCIATION + ".")
    execution = package == EXECUTION or package.startswith(EXECUTION + ".")
    research_publication = package == "market_research.publication"
    for node in ast.walk(ast.parse(text)):
        if research_publication and isinstance(node, ast.Call):
            called = node.func
            assert not (
                isinstance(called, ast.Attribute)
                and called.attr
                in {
                    "execute_batch",
                    "execute_job",
                    "compute",
                    "ensure",
                    "prepare_inputs",
                    "convert",
                    "construct_observations",
                    "observe",
                    "create_service",
                }
            ), "Publication cannot execute or acquire"
            assert not (
                isinstance(called, ast.Name)
                and called.id
                in {
                    "execute_batch",
                    "execute_job",
                    "compute",
                    "ensure",
                    "prepare_inputs",
                    "convert",
                    "construct_observations",
                    "observe",
                    "create_service",
                }
            ), "Publication cannot execute or acquire"
        if isinstance(node, ast.ImportFrom):
            names = [resolve_name("." * node.level + (node.module or ""), package)]
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        else:
            continue
        for name in names:
            if research_publication:
                allowed = {
                    "base64",
                    "collections.abc",
                    "sqlite3",
                    "threading",
                    "contextvars",
                    "functools",
                    "ntpath",
                    "errno",
                    "hashlib",
                    "json",
                    "math",
                    "os",
                    "re",
                    "stat",
                    "uuid",
                    "contextlib",
                    "dataclasses",
                    "datetime",
                    "pathlib",
                    "types",
                    "typing",
                    "data_lake",
                    "data_lake.datasets.tushare_index_daily",
                    "data_lake.datasets.tushare_trade_calendar",
                    "market_statistics",
                    "market_research.descriptive",
                    "market_research.descriptive.execution",
                    "market_research.descriptive.cases",
                    "market_research.publication._paths",
                    "market_research.publication._records",
                    "market_research.publication._sqlite",
                    "market_research.publication.errors",
                    "market_research.publication.source",
                    "market_research.publication.store",
                    "market_research.publication.visualization",
                }
                assert name in allowed, name
                if isinstance(node, ast.ImportFrom):
                    assert not {a.name for a in node.names} & {
                        "execute_batch",
                        "execute_job",
                        "compute",
                        "ensure",
                        "prepare_inputs",
                        "convert",
                        "construct_observations",
                        "observe",
                        "create_service",
                    }, name
                continue
            if publication:
                allowed_publication = {
                    "dataclasses": {"dataclass"},
                    "typing": {"Literal"},
                    CASE: {"DEFINITION"},
                    "market_statistics": {"QuantileSpec", "IntervalCountSpec"},
                }
                assert isinstance(node, ast.ImportFrom) and name in allowed_publication, name
                assert {alias.name for alias in node.names} <= allowed_publication[name]
                continue
            if execution:
                if name in EXECUTION_PUBLIC:
                    assert isinstance(node, ast.ImportFrom)
                    assert {alias.name for alias in node.names} <= EXECUTION_PUBLIC[name]
                else:
                    assert (
                        name in {"collections.abc", "dataclasses", "typing", "types"}
                        or name == EXECUTION
                        or name.startswith(EXECUTION + ".")
                    ), name
                continue
            assert name != EXECUTION and not name.startswith(EXECUTION + "."), name
            if isinstance(node, ast.ImportFrom):
                assert all(f"{name}.{alias.name}" != EXECUTION for alias in node.names), (
                    "Components cannot import execution through its parent package"
                )
            if basis_statistics and (
                name == "market_statistics" or name.startswith("market_statistics.")
            ):
                assert name == "market_statistics", name
                continue
            if basis_delivery and name == "market_statistics":
                assert isinstance(node, ast.ImportFrom)
                assert {a.name for a in node.names} <= {
                    "QuantileSpec",
                    "IntervalCountSpec",
                    "validate_spec",
                }
                continue
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
        check_imports(
            path.read_text(encoding="utf-8"),
            package,
            publication=path.relative_to(SOURCE).as_posix() == "descriptive/capabilities.py",
            basis_statistics=path.relative_to(SOURCE).as_posix()
            == "descriptive/cases/futures_basis/statistics.py",
            basis_delivery=path.relative_to(SOURCE).as_posix()
            in {
                "descriptive/cases/futures_basis/report.py",
                "descriptive/cases/futures_basis/evidence.py",
                "descriptive/cases/futures_basis/online.py",
                "descriptive/cases/futures_basis/online_record.py",
            },
        )


@pytest.mark.parametrize(
    "text",
    [
        "from market_statistics import compute",
        "from market_statistics.models import QuantileSpec",
        "from .cases.trailing_return import prepare_inputs",
        "import socket",
        "from .execution import execute_batch",
    ],
)
def test_capability_publication_cannot_execute_or_acquire(text: str) -> None:
    with pytest.raises(AssertionError):
        check_imports(text, "market_research.descriptive", publication=True)


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
        ("from ..execution import execute_job", CONVERSION),
        ("from ..execution import execute_job", OBSERVATION),
        ("from .. import execution", OBSERVATION),
        ("from market_research.descriptive import execution", ASSOCIATION),
        ("from ...execution import execute_job", CASE),
        ("from ..cases.trailing_return.inputs import validate_job", EXECUTION),
        ("from ..observation.models import ObservationSet", EXECUTION),
        ("from ..association.api import associate", EXECUTION),
        ("from ..conversion.validation import validate_source", EXECUTION),
        ("from market_statistics.api import compute", EXECUTION),
        ("import market_statistics", EXECUTION),
        ("from market_statistics import NumericSample", EXECUTION),
        ("from data_lake import OperationError", EXECUTION),
        ("from data_lake.datasets.tushare_index_daily import create_service", EXECUTION),
        ("import sqlite3", EXECUTION),
        ("import socket", EXECUTION),
        ("import random", EXECUTION),
        ("import time", EXECUTION),
    ],
)
def test_boundary_check_rejects_extra_permissions(text: str, package: str) -> None:
    with pytest.raises(AssertionError):
        check_imports(text, package)


@pytest.mark.parametrize(
    "text",
    [
        "from market_statistics import compute",
        "from market_research.descriptive.execution import execute_batch",
        "import market_statistics as st\nst.compute(None, None)",
        "from market_research.descriptive import execution as ex\nex.execute_batch(None)",
        "import requests",
    ],
)
def test_research_publication_cannot_execute_compute_or_fetch(text: str) -> None:
    with pytest.raises(AssertionError):
        check_imports(text, "market_research.publication")
