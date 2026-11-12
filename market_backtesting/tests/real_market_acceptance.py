"""Opt-in bounded real IM acceptance; run from the root with Poetry, not pytest.

Only the test harness redirects Dataset-owned storage, as DEVELOPMENT.md requires.
The application and all market operations use the published factories and APIs.
No default cache is read, modified or deleted. Artifacts contain public facts only.
"""

from __future__ import annotations

import importlib
import json
import tempfile
from contextlib import ExitStack
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

from market_backtesting.cases.futures_roll_long import (
    STRATEGY_PROFILES,
    FuturesRollApplicationError,
    FuturesRollRequest,
    analyze_futures_roll,
    create_futures_roll_service,
    replay_futures_roll,
)
from market_backtesting.cases.futures_roll_long.fingerprint import canonical_input_bytes


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="w2-wp3-real-im-"))
    report: dict[str, Any] = {
        "requested_window": ["2025-02-17", "2025-03-24"],
        "product_code": "IM",
        "status": "PENDING",
        "profiles": {},
    }
    # Test-only filesystem isolation. No private repository, Source or storage
    # facts are consumed, and no path is introduced into the public request/API.
    with ExitStack() as stack:
        for dataset in (
            "tushare_trade_calendar",
            "tushare_equity_index_futures",
            "tushare_index_daily",
        ):
            composition = importlib.import_module(f"data_lake.datasets.{dataset}._composition")
            stack.enter_context(
                patch.object(
                    composition,
                    "database_path",
                    lambda identity, *_: root / "cache" / f"{identity}.sqlite3",
                )
            )
        service = create_futures_roll_service()
        for profile in STRATEGY_PROFILES:
            request = FuturesRollRequest("IM", date(2025, 2, 17), date(2025, 3, 24), profile)
            try:
                result = service.run(request)
            except FuturesRollApplicationError as exc:
                underlying_message = str(exc.__context__).lower()
                diagnostic_reason = (
                    "source_credential_unavailable"
                    if "token" in underlying_message or "credential" in underlying_message
                    else "public_operation_unavailable"
                )
                report["profiles"][profile] = {
                    "status": "NOT RUN",
                    "diagnostic_reason": diagnostic_reason,
                    "stage": exc.stage,
                    "dependency": exc.dependency,
                    "category": exc.category,
                    "reason": exc.reason,
                    "ensure_diagnostics": [asdict(item) for item in exc.diagnostics],
                }
                # Do not repeat Source attempts for the same failed dependency/window.
                break
            try:
                assert result.replay.rolls, "window contains no observed roll"
                assert result.replay.replay.final_portfolio.position is None
                replayed = replay_futures_roll(result.inputs.replay_input)
                assert replayed == result.replay
                assert analyze_futures_roll(replayed) == result.performance
                repeated = service.run(request)
                assert repeated.replay == result.replay
                assert repeated.performance == result.performance
                assert repeated.inputs.exports == result.inputs.exports
                assert repeated.input_fingerprint == result.input_fingerprint
                for roll in result.replay.rolls:
                    position = result.replay.sessions.index(roll.trade_date)
                    record = result.replay.replay.daily[position]
                    assert result.replay.daily[position].pnl_contract_code == roll.old_contract_code
                    assert record.transition.next_portfolio.position is not None
                    assert (
                        record.transition.next_portfolio.position.reference_price == roll.new_close
                    )
                    old = next(
                        row
                        for row in result.inputs.exports.futures.records
                        if row.trade_date == roll.trade_date
                        and row.contract_code == roll.old_contract_code
                    )
                    assert old.delist_date == roll.trade_date
                    previous = next(
                        row
                        for row in result.inputs.exports.futures.records
                        if row.trade_date == result.replay.sessions[position - 1]
                        and row.contract_code == roll.old_contract_code
                    )
                    expected_pnl = (old.close - previous.close) * old.multiplier
                    assert result.performance.daily[position].daily_pnl == expected_pnl
                assert (
                    tuple(row.trade_date for row in result.inputs.replay_input.index_closes)
                    == result.replay.sessions
                )
                first_index = result.inputs.replay_input.index_closes[0].close
                for day, index_close in zip(
                    result.performance.daily, result.inputs.replay_input.index_closes, strict=True
                ):
                    assert day.benchmark_close == index_close.close
                    assert day.benchmark_cumulative_return == index_close.close / first_index - 1

            except AssertionError as exc:
                report["profiles"][profile] = {"status": "FAIL", "reason": str(exc)}
                break
            (root / "canonical-inputs.json").write_bytes(
                canonical_input_bytes(result.inputs.exports)
            )
            report["profiles"][profile] = {
                "status": "PASS",
                "fingerprint": result.input_fingerprint,
                "observed_window": [result.observed_start_date, result.observed_end_date],
                "sessions": len(result.replay.sessions),
                "futures_rows": len(result.inputs.exports.futures.records),
                "index_calendar_coverage": asdict(result.inputs.index_calendar_export.coverage),
                "coverage": {
                    name: asdict(getattr(result.inputs.exports, name).coverage)
                    for name in ("calendar_cffex", "futures", "index")
                },
                "summary": asdict(result.performance.summary),
                "rolls": [asdict(roll) for roll in result.replay.rolls],
                "reproduction": "PASS",
                "final_flat": True,
            }
    for profile in STRATEGY_PROFILES:
        report["profiles"].setdefault(
            profile, {"status": "NOT RUN", "reason": "prior_dependency_failure"}
        )
    statuses = [item["status"] for item in report["profiles"].values()]
    report["status"] = (
        "PASS"
        if all(status == "PASS" for status in statuses)
        else "FAIL"
        if "FAIL" in statuses
        else "NOT RUN"
    )
    destination = root / "acceptance.json"
    destination.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "artifact": str(destination),
                "profiles": report["profiles"],
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
