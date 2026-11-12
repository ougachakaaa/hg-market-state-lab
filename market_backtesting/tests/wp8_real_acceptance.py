"""Opt-in WP8 real IM acceptance. Never run by pytest; never uses default caches.

From repository root: poetry run python market_backtesting/tests/wp8_real_acceptance.py
  --root /absolute/external/artifact-directory --mode python|serve|reproduce
Storage redirection follows real_market_acceptance.py; all facts use public services.
"""

from __future__ import annotations

import argparse
import importlib
import json
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

from data_lake import OperationError
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service
from market_backtesting.cases.futures_roll_long import (
    STRATEGY_PROFILES,
    FuturesRollApplicationError,
    FuturesRollError,
    FuturesRollRequest,
    build_backtest_result,
    build_evidence_package,
    create_futures_roll_service,
    encode_evidence_package,
    reproduce_futures_roll_evidence,
    validate_backtest_result,
)

START, END = date(2024, 1, 1), date(2026, 10, 30)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, default=str, indent=2, allow_nan=False) + "\n")


@contextmanager
def isolated_cache(root: Path) -> Iterator[None]:
    """Redirect only factory filesystem placement, not service behavior or data."""
    with ExitStack() as stack:
        for dataset in (
            "tushare_trade_calendar", "tushare_equity_index_futures", "tushare_index_daily"
        ):
            composition = importlib.import_module(f"data_lake.datasets.{dataset}._composition")
            stack.enter_context(patch.object(
                composition, "database_path",
                lambda identity, *_: root / "cache" / f"{identity}.sqlite3",
            ))
        yield


def coverage_snapshot() -> dict[str, Any]:
    """Public exports only; incomplete prerequisites remain unknown."""
    report: dict[str, Any] = {}
    for exchange in ("CFFEX", "SSE"):
        try:
            export = create_service().export(TradeCalendarRange(exchange, START, END))
            report[exchange] = {"coverage": asdict(export.coverage),
                                "schema": export.export_schema_version,
                                "rows": len(export.records)}
        except OperationError:
            report[exchange] = {"state": "unavailable"}
    return report


def diagnostic_counts(exc: FuturesRollApplicationError) -> list[dict[str, Any]]:
    # UnitFailure.reason may contain provider details: keep only numerical counters.
    return [{"dependency": item.dependency, **{
        key: value for key, value in asdict(item.result).items() if key != "failures"
    }} for item in exc.diagnostics]


def accept_python(root: Path) -> None:
    service = create_futures_roll_service()
    request = FuturesRollRequest("IM", START, END, STRATEGY_PROFILES[0])
    before = sorted(str(path.relative_to(root)) for path in root.rglob("*.sqlite3"))
    report: dict[str, Any] = {
        "kind": "actual_real_market", "request": asdict(request),
        "preflight": asdict(service.preflight(request)),
        "calendar_before": coverage_snapshot(), "profiles": {},
    }
    assert before == sorted(str(path.relative_to(root)) for path in root.rglob("*.sqlite3"))
    report["preflight_created_no_database"] = True
    write_json(root / "python-acceptance.json", report)
    for profile in STRATEGY_PROFILES:
        request = FuturesRollRequest("IM", START, END, profile)
        started = time.monotonic()
        print(json.dumps({"phase": "python_run", "profile": profile}), flush=True)
        try:
            execution = service.run(request)
        except FuturesRollApplicationError as exc:
            report["profiles"][profile] = {
                "status": "NOT RUN" if exc.category in {
                    "upstream_operation", "incomplete_input"
                } else "FAIL", "stage": exc.stage, "dependency": exc.dependency,
                "category": exc.category, "reason": exc.reason,
                "ensure": diagnostic_counts(exc), "seconds": time.monotonic() - started,
            }
            # Do not repeat acquisition against a known unavailable dependency.
            break
        result = build_backtest_result(execution)
        validate_backtest_result(result, execution)
        assert execution.replay.replay.final_portfolio.position is None
        assert result.daily[-1].position_contract_code is None
        assert result.summary.execution_count == 2 + 2 * result.summary.roll_count
        assert result.window.cffex_session_count == len(execution.replay.sessions)
        rows = {(row.trade_date, row.contract_code): row
                for row in execution.inputs.exports.futures.records}
        for roll in result.rolls:
            old, new = rows[roll.trade_date, roll.old_contract_code], rows[
                roll.trade_date, roll.new_contract_code]
            assert old.delist_date == roll.trade_date
            assert old.close == roll.old_close and new.close == roll.new_close
            assert roll.new_slot == ("M1" if "M1" in profile else "Q1")
        for day, record, analyzed in zip(
            result.daily, execution.replay.replay.daily, execution.performance.daily, strict=True
        ):
            assert day.daily_pnl == record.transition.daily_pnl
            assert day.daily_return == analyzed.daily_return
            assert day.cumulative_return == analyzed.cumulative_return
        payload = encode_evidence_package(build_evidence_package(execution, result))
        (root / f"{profile}-evidence.json").write_bytes(payload)
        write_json(root / f"{profile}-result.json", asdict(result))
        write_json(root / f"{profile}-sse-calendar.json", asdict(
            execution.inputs.index_calendar_export))
        report["profiles"][profile] = {
            "status": "PASS", "fingerprint": result.evidence.input_fingerprint,
            "window": asdict(result.window), "summary": asdict(result.summary),
            "rolls": [asdict(item) for item in result.rolls],
            "coverage": [asdict(item) for item in result.evidence.coverage],
            "sources": asdict(result.evidence).get("sources"),
            "result_bytes": (root / f"{profile}-result.json").stat().st_size,
            "evidence_bytes": len(payload), "seconds": time.monotonic() - started,
            "final_flat": True, "financial_invariants": "PASS",
            "ensure": [{"dependency": item.dependency, **{
                key: value for key, value in asdict(item.result).items() if key != "failures"
            }} for item in execution.inputs.diagnostics],
        }
        write_json(root / "python-acceptance.json", report)
    for profile in STRATEGY_PROFILES:
        report["profiles"].setdefault(profile, {
            "status": "NOT RUN", "reason": "prior_dependency_failure"})
    report["calendar_after"] = coverage_snapshot()
    report["preflight_after"] = asdict(service.preflight(request))
    complete = all(item["status"] == "PASS" for item in report["profiles"].values())
    report["status"] = "PASS" if complete else (
        "FAIL" if any(item["status"] == "FAIL" for item in report["profiles"].values())
        else "PARTIAL"
    )
    if complete:
        report["same_input"] = len({item["fingerprint"] for item in
                                    report["profiles"].values()}) == 1
        assert report["same_input"], "public_inputs_changed_between_profiles"
    write_json(root / "python-acceptance.json", report)
    print(json.dumps({"phase": "python_finished", "status": report["status"]}), flush=True)


def reproduce(root: Path) -> None:
    report: dict[str, Any] = {}
    for profile in STRATEGY_PROFILES:
        path = root / f"{profile}-evidence.json"
        if not path.exists():
            report[profile] = {"status": "NOT RUN", "reason": "no_real_evidence"}
            continue
        started = time.monotonic()
        verified = reproduce_futures_roll_evidence(path.read_bytes())
        expected = json.loads((root / f"{profile}-result.json").read_text())
        assert json.loads(json.dumps(asdict(verified.result), default=str)) == expected
        report[profile] = {"status": verified.status,
                           "fingerprint": verified.input_fingerprint,
                           "events": verified.state_event_count,
                           "seconds": time.monotonic() - started}
    write_json(root / "reproduction.json", report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--mode", choices=("python", "serve", "reproduce"), required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not args.root.is_absolute() or root.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error("root must be an absolute artifact directory outside the repository")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.mode == "reproduce":
        reproduce(root)
    else:
        with isolated_cache(root):
            if args.mode == "python":
                try:
                    accept_python(root)
                except (FuturesRollError, AssertionError) as exc:
                    report = json.loads((root / "python-acceptance.json").read_text())
                    report["status"] = "FAIL"
                    report["failure"] = {
                        "category": exc.category if isinstance(exc, FuturesRollError)
                        else "acceptance_invariant",
                        "reason": exc.reason if isinstance(exc, FuturesRollError)
                        else "acceptance_invariant",
                    }
                    write_json(root / "python-acceptance.json", report)
                    raise SystemExit(1) from None
                if json.loads((root / "python-acceptance.json").read_text())["status"] == "FAIL":
                    raise SystemExit(1)
            else:
                import uvicorn

                from ui_http.app import create_app
                uvicorn.run(create_app(), host="127.0.0.1", port=8011, proxy_headers=False)


if __name__ == "__main__":
    main()
