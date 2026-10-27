"""Batch may validate/inspect public carriers, but only Single Job executes components."""

import ast
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/market_research/descriptive/execution"
ALLOWED = {
    "dataclasses": {"dataclass"},
    "typing": {"Literal"},
    "collections.abc": {"Mapping", "Sequence", "Set"},
    "types": {"MappingProxyType"},
    "..association": {"AnalysisRequest", "ResearchAnalysisEvidence"},
    "..cases.trailing_return": {"PreparedInputs"},
    "..conversion": {"SampleProjection"},
    "..observation": {"DateWindow", "JobIdentity", "ObservationJobSpec", "ObservationSet"},
    ".models": {"AnalysisOutcome", "FailureRecord", "JobResult", "InvalidPlan"},
    ".plan": {"ResearchPlan", "preflight_plan"},
}


def check_batch_imports(text: str, *, plan: bool = False) -> None:
    allowed = {**ALLOWED, ".api": {"_preflight"} if plan else {"execute_job"}}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            raise AssertionError(
                "Batch imports only precise public carriers and execution operations"
            )
        if isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            assert module in allowed, module
            assert {alias.name for alias in node.names} <= allowed[module], module


def test_batch_and_plan_only_use_their_precise_dependencies() -> None:
    check_batch_imports((SOURCE / "batch.py").read_text(encoding="utf-8"))
    check_batch_imports((SOURCE / "plan.py").read_text(encoding="utf-8"), plan=True)


@pytest.mark.parametrize(
    "text",
    [
        "from market_statistics import compute",
        "from market_statistics import validate_spec",
        "from ..conversion import convert",
        "from ..association import associate",
        "from ..cases.trailing_return import construct_observations",
        "from ..cases.trailing_return import prepare_inputs",
        "from data_lake.datasets.tushare_index_daily import create_service",
        "from .api import compute",
        "from .api import prepare_inputs",
        "from .api import _preflight",
        "from . import api",
        "import market_statistics",
        "import sqlite3",
    ],
)
def test_batch_architecture_rejects_direct_component_execution(text: str) -> None:
    with pytest.raises(AssertionError):
        check_batch_imports(text)
