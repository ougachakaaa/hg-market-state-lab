"""Architectural checks for the isolated pure holding-simulation package."""

from __future__ import annotations

import ast
import tomllib
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import market_backtesting
from market_backtesting import (
    ContractClose,
    DailyHolding,
    DecisionSlotEvidence,
    Execution,
    HoldingSimulationInput,
    RollEvent,
    SessionFacts,
    StrategyTimeline,
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
}
FORBIDDEN_W1_SEMANTICS = {
    "detect_contract_transitions",
    "CandidateSessions",
    "ContractTransition",
    "AbsenceBoundary",
    "TransitionResult",
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
                    if alias.name == "market_research" or alias.name.startswith(
                        "market_research."
                    ):
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


def test_no_market_io_or_generic_framework_dependencies() -> None:
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
            elif isinstance(node, ast.ClassDef):
                if any(word in node.name for word in ("Engine", "Registry", "Provider")):
                    violations.append(f"{path}: class {node.name}")
    assert not violations, "\n".join(violations)


def test_no_unauthorized_w1_transition_or_research_semantics() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_files())
    present = sorted(name for name in FORBIDDEN_W1_SEMANTICS if name in text)
    assert not present, present


def test_public_api_tree_is_frozen() -> None:
    expected = (
        HoldingSimulationInput,
        SessionFacts,
        ContractClose,
        DecisionSlotEvidence,
        DailyHolding,
        Execution,
        RollEvent,
        StrategyTimeline,
    )
    for carrier in expected:
        assert is_dataclass(carrier)
        params = cast(Any, carrier).__dataclass_params__
        assert params.frozen
        assert all(field.name for field in fields(carrier))
    for name in (
        "simulate_holding",
        "HoldingSimulationError",
        "PRODUCT_CODES",
        "STRATEGY_PROFILES",
    ):
        assert getattr(market_backtesting, name) is not None
    assert market_backtesting.PRODUCT_CODES == ("IF", "IH", "IC", "IM")
    assert market_backtesting.STRATEGY_PROFILES == (
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
    assert "market_backtesting" in manifest["tool"]["ruff"]["lint"]["isort"][
        "known-first-party"
    ]


def test_no_module_local_python_project_or_environment() -> None:
    package_root = ROOT / "market_backtesting"
    assert not (package_root / "pyproject.toml").exists()
    assert not (package_root / "poetry.lock").exists()
    assert not (package_root / ".venv").exists()


def test_source_has_no_datalake_or_http_imports() -> None:
    forbidden_roots = {
        "data_lake",
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
    violations: list[str] = []
    for path in source_files():
        for name in imported_modules(path):
            if name.split(".", 1)[0] in forbidden_roots:
                violations.append(f"{path}: {name}")
    assert not violations, "\n".join(violations)
