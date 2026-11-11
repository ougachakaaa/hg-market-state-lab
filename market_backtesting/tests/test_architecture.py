"""Ownership and dependency guards for the pure Core and W2 Policy."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
import tomllib
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import market_backtesting.cases.futures_roll_long as case_api
import market_backtesting.core as core_api
from market_backtesting.cases.futures_roll_long import (
    ContractClose,
    DailyPerformance,
    DailyProjection,
    DecisionSlotEvidence,
    Execution,
    FuturesRollInput,
    FuturesRollPerformance,
    FuturesRollReplay,
    IndexClose,
    PerformanceSummary,
    RollEvent,
    SessionFacts,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "market_backtesting/src/market_backtesting"
ALLOWED_W1_MODULE = "market_research.descriptive.cases.futures_basis"
ALLOWED_W1_NAMES = {
    "resolve_daily_slots",
    "ContractMetadata",
    "DailyUniverseEvidence",
    "DailySlotResolution",
    "SlotMapping",
    "SlotResolutionError",
    "SLOTS",
}
ALLOWED_TOP_LEVEL = {
    "__future__",
    "dataclasses",
    "datetime",
    "math",
    "typing",
    "market_research",
    "collections",
    "data_lake",
    "hashlib",
    "json",
    "re",
    "zoneinfo",
}
FORBIDDEN_W1_SEMANTICS = {
    "detect_contract_transitions",
    "CandidateSessions",
    "ContractTransition",
    "AbsenceBoundary",
    "construct_observations",
    "observe_futures_basis",
    "preflight_inputs",
    "FuturesBasisOnlineApplication",
    "compose_report",
    "analyze_distribution",
}


def source_files() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


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


def test_only_authorized_w1_symbols_are_imported() -> None:
    violations: list[str] = []
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "market_research" or alias.name.startswith("market_research."):
                        violations.append(f"{path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and not node.level:
                module = node.module or ""
                if module == "market_research" or module.startswith("market_research."):
                    if module != ALLOWED_W1_MODULE:
                        violations.append(f"{path}: from {module}")
                        continue
                    names = {alias.name for alias in node.names}
                    if not names <= ALLOWED_W1_NAMES:
                        violations.append(f"{path}: {sorted(names - ALLOWED_W1_NAMES)}")
    assert not violations, "\n".join(violations)


def test_dependencies_are_limited_to_public_market_inputs_and_standard_library() -> None:
    violations: list[str] = []
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root not in ALLOWED_TOP_LEVEL:
                        violations.append(f"{path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and not node.level:
                root = (node.module or "").split(".", 1)[0]
                if root not in ALLOWED_TOP_LEVEL:
                    violations.append(f"{path}: from {node.module}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"open", "eval", "exec", "__import__"}:
                    violations.append(f"{path}: call {node.func.id}")
    assert not violations, "\n".join(violations)


def test_no_unauthorized_w1_transition_or_research_semantics() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_files())
    present = sorted(name for name in FORBIDDEN_W1_SEMANTICS if name in text)
    assert not present, present


def test_public_api_tree_is_frozen() -> None:
    expected = (
        FuturesRollInput,
        SessionFacts,
        ContractClose,
        DecisionSlotEvidence,
        DailyProjection,
        Execution,
        RollEvent,
        FuturesRollReplay,
        IndexClose,
        DailyPerformance,
        PerformanceSummary,
        FuturesRollPerformance,
    )
    for carrier in expected:
        assert is_dataclass(carrier)
        params = cast(Any, carrier).__dataclass_params__
        assert params.frozen
        assert all(field.name for field in fields(carrier))
    for name in (
        "replay_futures_roll",
        "analyze_futures_roll",
        "FuturesRollError",
        "PRODUCT_CODES",
        "STRATEGY_PROFILES",
    ):
        assert getattr(case_api, name) is not None
    assert case_api.PRODUCT_CODES == ("IF", "IH", "IC", "IM")
    assert case_api.STRATEGY_PROFILES == (
        "expiry_to_M1_v1",
        "expiry_to_Q1_v1",
    )


def test_root_packaging_and_tool_registrations() -> None:
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert {"include": "market_backtesting", "from": "market_backtesting/src"} in (
        manifest["tool"]["poetry"]["packages"]
    )
    pytest_config = manifest["tool"]["pytest"]["ini_options"]
    assert "market_backtesting/tests" in pytest_config["testpaths"]
    assert "market_backtesting/src" in pytest_config["pythonpath"]
    assert {
        "market_backtesting/src",
        "market_backtesting/tests",
    } <= set(manifest["tool"]["ruff"]["src"])
    assert {
        "market_backtesting/src",
        "market_backtesting/tests",
    } <= set(manifest["tool"]["mypy"]["files"])
    assert "market_backtesting/src" in manifest["tool"]["mypy"]["mypy_path"]
    assert "market_backtesting/tests" in manifest["tool"]["mypy"]["mypy_path"]
    assert "market_backtesting" in manifest["tool"]["ruff"]["lint"]["isort"]["known-first-party"]


def test_no_module_local_python_project_or_environment() -> None:
    package_root = ROOT / "market_backtesting"
    assert not (package_root / "pyproject.toml").exists()
    assert not (package_root / "poetry.lock").exists()
    assert not (package_root / ".venv").exists()


def test_source_uses_only_authorized_datalake_public_boundaries() -> None:
    forbidden_roots = {
        "data_snapshot",
        "market_statistics",
        "market_modeling",
        "ui_cli",
        "ui_http",
        "fastapi",
        "starlette",
        "uvicorn",
        "sqlite3",
        "pathlib",
        "os",
        "requests",
        "urllib",
        "httpx",
    }
    allowed_datalake = {
        "data_lake",
        "data_lake.datasets.tushare_trade_calendar",
        "data_lake.datasets.tushare_equity_index_futures",
        "data_lake.datasets.tushare_index_daily",
    }
    input_modules = {
        "application_models.py",
        "input_validation.py",
        "public_inputs.py",
        "fingerprint.py",
        "application.py",
        "preflight.py",
    }
    violations: list[str] = []
    for path in source_files():
        for name in imported_modules(path):
            if name.split(".", 1)[0] == "data_lake":
                if (
                    name not in allowed_datalake
                    or path.name not in input_modules
                    or not path.is_relative_to(SOURCE / "cases/futures_roll_long")
                ):
                    violations.append(f"{path}: {name}")
            if name.split(".", 1)[0] in forbidden_roots:
                violations.append(f"{path}: {name}")
    assert not violations, "\n".join(violations)


def resolved_dependencies(path: Path) -> list[str]:
    relative = path.relative_to(SOURCE).with_suffix("")
    parts = ("market_backtesting", *relative.parts)
    package = ".".join(parts[:-1])
    imports: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                module = importlib.util.resolve_name(
                    "." * node.level + (node.module or ""), package
                )
            else:
                module = node.module or ""
            imports.append(module)
            imports.extend(module + "." + alias.name for alias in node.names)
    return imports


def test_core_and_parent_initializers_are_isolated_from_cases_and_business_modules() -> None:
    paths = list((SOURCE / "core").glob("*.py")) + [SOURCE / "__init__.py"]
    for path in paths:
        for imported in resolved_dependencies(path):
            root = imported.split(".")[0]
            assert root in {
                "__future__",
                "collections",
                "dataclasses",
                "datetime",
                "math",
                "typing",
                "market_backtesting",
            }, (path, imported)
            if root == "market_backtesting":
                assert imported == "market_backtesting" or imported.startswith(
                    "market_backtesting.core"
                ), (path, imported)
    for path in source_files():
        for imported in resolved_dependencies(path):
            if imported.startswith("market_research"):
                assert path.is_relative_to(SOURCE / "cases/futures_roll_long"), (path, imported)


def test_core_import_works_with_business_imports_blocked() -> None:
    code = """
import importlib.abc
import sys
class BlockBusiness(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'market_research', 'data_lake', 'data_snapshot', 'ui_http'}:
            raise AssertionError('Core tried to load ' + fullname)
sys.meta_path.insert(0, BlockBusiness())
from market_backtesting.core import Portfolio, replay, transition_portfolio, account
assert Portfolio().position is None
assert all(callable(fn) for fn in (replay, transition_portfolio, account))
assert not any(name.startswith('market_backtesting.cases') for name in sys.modules)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr


def test_core_public_carriers_are_frozen_and_legacy_pipeline_is_absent() -> None:
    for name in (
        "InstrumentReference",
        "Position",
        "Portfolio",
        "TargetPortfolio",
        "DailyMarketSnapshot",
        "TransitionResult",
        "AccountingState",
        "DailyRecord",
        "ReplayResult",
    ):
        carrier = getattr(core_api, name)
        assert is_dataclass(carrier) and cast(Any, carrier).__dataclass_params__.frozen
    assert not any((SOURCE / name).exists() for name in ("holding.py", "models.py", "failures.py"))
    definitions = [
        node.name
        for path in source_files()
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.FunctionDef)
    ]
    for name in ("replay", "transition_portfolio", "account"):
        assert definitions.count(name) == 1
    assert "simulate_holding" not in definitions


def test_pure_case_computation_does_not_depend_on_public_input_orchestration() -> None:
    pure = ("policy.py", "replay.py", "performance.py", "validation.py", "models.py")
    input_concerns = (
        "application",
        "application_models",
        "input_validation",
        "public_inputs",
        "preflight",
        "fingerprint",
    )
    for filename in pure:
        path = SOURCE / "cases/futures_roll_long" / filename
        for imported in resolved_dependencies(path):
            assert not imported.startswith("data_lake"), (path, imported)
            assert not any(
                imported == f"market_backtesting.cases.futures_roll_long.{concern}"
                or imported.startswith(f"market_backtesting.cases.futures_roll_long.{concern}.")
                for concern in input_concerns
            ), (path, imported)


def test_datalake_imports_name_only_published_symbols() -> None:
    published = {
        "data_lake": {
            "CoverageResult",
            "EnsureResult",
            "UnitFailure",
            "ExportEnvelope",
            "InvalidRequestError",
            "OperationError",
        },
        "data_lake.datasets.tushare_trade_calendar": {
            "TradeCalendarExport",
            "TradeCalendarRange",
            "TradeCalendarRecord",
            "create_service",
        },
        "data_lake.datasets.tushare_equity_index_futures": {
            "FuturesDailyExport",
            "FuturesDailyRange",
            "FuturesDailyRow",
            "create_service",
        },
        "data_lake.datasets.tushare_index_daily": {
            "IndexDailyExport",
            "IndexDailyRange",
            "IndexDailyRow",
            "create_service",
        },
    }
    for path in source_files():
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith("data_lake") for alias in node.names), path
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("data_lake"):
                assert {alias.name for alias in node.names} <= published.get(
                    node.module or "", set()
                ), path
