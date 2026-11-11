"""Reconcile existing WP3/WP4 classifications before online storage exists."""

from dataclasses import asdict

import pytest

from market_backtesting.cases.futures_roll_long import FuturesRollApplicationError, FuturesRollError
from market_backtesting.cases.futures_roll_long.online_models import project_failure


@pytest.mark.parametrize("stage", ["request", "export", "ensure", "prepare", "replay", "analysis"])
def test_existing_application_stage_is_preserved(stage: str) -> None:
    exc = FuturesRollApplicationError(
        "incomplete_input", "final_export_incomplete", stage=stage, dependency="calendar_sse"
    )
    assert asdict(project_failure(exc)) == dict(
        stage=stage,
        category="incomplete_input",
        dependency="calendar_sse",
        reason="final_export_incomplete",
    )


@pytest.mark.parametrize(
    "category,reason",
    [
        ("invalid_numeric", "daily_pnl"),
        ("invalid_accounting", "session_already_accounted"),
        ("invalid_result", "result_projection_mismatch"),
        ("invalid_evidence", "incomplete_retained_inputs"),
        ("invalid_case_input", "insufficient_sessions"),
    ],
)
def test_case_failure_preserves_meaning(category: str, reason: str) -> None:
    failure = project_failure(FuturesRollError(category, reason), "result_validation")
    assert (failure.stage, failure.category, failure.reason) == (
        "result_validation",
        category,
        reason,
    )


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("credential /private/path traceback"),
        FuturesRollError("invalid_numeric", "/private/path"),
        FuturesRollApplicationError("invalid_request", "invalid_case", stage="secret"),
    ],
)
def test_unknown_exception_is_fixed_safe_failure(exc: Exception) -> None:
    assert asdict(project_failure(exc)) == dict(
        stage="execution", category="internal_failure", dependency=None, reason="internal_failure"
    )


@pytest.mark.parametrize(
    "category,reason",
    [
        ("upstream_operation", "upstream_request_rejected"),
        ("missing_market_fact", "missing_contract_row"),
        ("accounting_failure", "entry_multiplier"),
    ],
)
def test_conditional_and_numeric_reasons_are_preserved(category: str, reason: str) -> None:
    failure = project_failure(FuturesRollApplicationError(category, reason, stage="replay"))
    assert (failure.category, failure.reason, failure.stage) == (category, reason, "replay")


def test_direct_core_error_is_preserved() -> None:
    from market_backtesting.core import CoreError

    failure = project_failure(
        CoreError("invalid_accounting", "session_already_accounted"), "replay"
    )
    assert failure.stage == "replay" and failure.category == "invalid_accounting"
