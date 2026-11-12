"""Opt-in WP8 real IM acceptance. Never run by pytest; never uses default caches.

From repository root::

    poetry run python market_backtesting/tests/wp8_real_acceptance.py \\
        --root /absolute/external/artifact-directory --mode python
    poetry run python market_backtesting/tests/wp8_real_acceptance.py \\
        --root /absolute/external/artifact-directory --mode reproduce

Exit codes: 0 PASS, 1 FAIL, 2 PARTIAL, 3 NOT RUN (including missing evidence).
Storage redirection follows real_market_acceptance.py; all facts use public services.
"""

from __future__ import annotations

import argparse
import importlib
import json
import time
import uuid
from collections.abc import Iterable, Iterator, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from datetime import UTC, date, datetime
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
REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ACCEPTANCE = "python-acceptance.json"
REPRODUCTION_ACCEPTANCE = "offline-reproduction.json"

PASS, FAIL, PARTIAL, NOT_RUN = "PASS", "FAIL", "PARTIAL", "NOT RUN"
EXIT_CODES = {PASS: 0, FAIL: 1, PARTIAL: 2, NOT_RUN: 3}


def exit_code(status: str) -> int:
    """PASS is the only successful gate; unknown artifacts fail closed."""
    return EXIT_CODES.get(status, EXIT_CODES[FAIL])


def overall_status(statuses: Iterable[str]) -> str:
    """Keep the strongest failure; a PASS requires every required stage to pass."""
    values = tuple(statuses)
    if values and all(value == PASS for value in values):
        return PASS
    if FAIL in values:
        return FAIL
    if PARTIAL in values:
        return PARTIAL
    if PASS in values:
        return PARTIAL
    return NOT_RUN


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, default=str, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def new_report(kind: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "status": "RUNNING",
        "run_id": uuid.uuid4().hex,
        "generated_at": datetime.now(UTC).isoformat(),
        "profiles": {},
    }


def clear_previous_run(root: Path) -> None:
    """A new acceptance round must never reuse this round's PASS artifacts."""
    for profile in STRATEGY_PROFILES:
        for suffix in ("-result.json", "-evidence.json", "-sse-calendar.json"):
            (root / f"{profile}{suffix}").unlink(missing_ok=True)
    for name in (REPRODUCTION_ACCEPTANCE, "reproduction.json"):
        (root / name).unlink(missing_ok=True)


@contextmanager
def isolated_cache(root: Path) -> Iterator[None]:
    """Redirect only factory filesystem placement, not service behavior or data."""
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
        yield


def coverage_snapshot() -> dict[str, Any]:
    """Public exports only; incomplete prerequisites remain unknown."""
    report: dict[str, Any] = {}
    for exchange in ("CFFEX", "SSE"):
        try:
            export = create_service().export(TradeCalendarRange(exchange, START, END))
            report[exchange] = {
                "coverage": asdict(export.coverage),
                "schema": export.export_schema_version,
                "rows": len(export.records),
            }
        except OperationError:
            report[exchange] = {"state": "unavailable"}
    return report


def diagnostic_counts(exc: FuturesRollApplicationError) -> list[dict[str, Any]]:
    # UnitFailure.reason may contain provider details: keep only numerical counters.
    return [
        {
            "dependency": item.dependency,
            **{
                key: value
                for key, value in asdict(item.result).items()
                if key != "failures"
            },
        }
        for item in exc.diagnostics
    ]


def fail_report(report: dict[str, Any], root: Path, exc: BaseException) -> str:
    report["status"] = FAIL
    if isinstance(exc, FuturesRollError):
        report["failure"] = {"category": exc.category, "reason": exc.reason}
    else:
        report["failure"] = {"category": "acceptance_error", "reason": type(exc).__name__}
    write_json(root / PYTHON_ACCEPTANCE, report)
    return FAIL


def accept_python(root: Path) -> str:
    report = new_report("actual_real_market")
    # Invalidate any earlier PASS before cleanup or the first real operation starts.
    write_json(root / PYTHON_ACCEPTANCE, report)
    try:
        clear_previous_run(root)
        service = create_futures_roll_service()
        request = FuturesRollRequest("IM", START, END, STRATEGY_PROFILES[0])
        before = sorted(str(path.relative_to(root)) for path in root.rglob("*.sqlite3"))
        report.update(
            {
                "request": asdict(request),
                "preflight": asdict(service.preflight(request)),
                "calendar_before": coverage_snapshot(),
            }
        )
        assert before == sorted(str(path.relative_to(root)) for path in root.rglob("*.sqlite3"))
        report["preflight_created_no_database"] = True
        write_json(root / PYTHON_ACCEPTANCE, report)
        for profile in STRATEGY_PROFILES:
            request = FuturesRollRequest("IM", START, END, profile)
            started = time.monotonic()
            print(json.dumps({"phase": "python_run", "profile": profile}), flush=True)
            try:
                execution = service.run(request)
            except FuturesRollApplicationError as exc:
                report["profiles"][profile] = {
                    "status": NOT_RUN
                    if exc.category in {"upstream_operation", "incomplete_input"}
                    else FAIL,
                    "stage": exc.stage,
                    "dependency": exc.dependency,
                    "category": exc.category,
                    "reason": exc.reason,
                    "ensure": diagnostic_counts(exc),
                    "seconds": time.monotonic() - started,
                }
                # Do not repeat acquisition against a known unavailable dependency.
                break
            result = build_backtest_result(execution)
            validate_backtest_result(result, execution)
            assert execution.replay.replay.final_portfolio.position is None
            assert result.daily[-1].position_contract_code is None
            assert result.summary.execution_count == 2 + 2 * result.summary.roll_count
            assert result.window.cffex_session_count == len(execution.replay.sessions)
            rows = {
                (row.trade_date, row.contract_code): row
                for row in execution.inputs.exports.futures.records
            }
            for roll in result.rolls:
                old, new = (
                    rows[roll.trade_date, roll.old_contract_code],
                    rows[roll.trade_date, roll.new_contract_code],
                )
                assert old.delist_date == roll.trade_date
                assert old.close == roll.old_close and new.close == roll.new_close
                assert roll.new_slot == ("M1" if "M1" in profile else "Q1")
            for day, record, analyzed in zip(
                result.daily,
                execution.replay.replay.daily,
                execution.performance.daily,
                strict=True,
            ):
                assert day.daily_pnl == record.transition.daily_pnl
                assert day.daily_return == analyzed.daily_return
                assert day.cumulative_return == analyzed.cumulative_return
            payload = encode_evidence_package(build_evidence_package(execution, result))
            (root / f"{profile}-evidence.json").write_bytes(payload)
            write_json(root / f"{profile}-result.json", asdict(result))
            write_json(
                root / f"{profile}-sse-calendar.json",
                asdict(execution.inputs.index_calendar_export),
            )
            report["profiles"][profile] = {
                "status": PASS,
                "fingerprint": result.evidence.input_fingerprint,
                "window": asdict(result.window),
                "summary": asdict(result.summary),
                "rolls": [asdict(item) for item in result.rolls],
                "coverage": [asdict(item) for item in result.evidence.coverage],
                "sources": asdict(result.evidence).get("sources"),
                "result_bytes": (root / f"{profile}-result.json").stat().st_size,
                "evidence_bytes": len(payload),
                "seconds": time.monotonic() - started,
                "final_flat": True,
                "financial_invariants": PASS,
                "ensure": [
                    {
                        "dependency": item.dependency,
                        **{
                            key: value
                            for key, value in asdict(item.result).items()
                            if key != "failures"
                        },
                    }
                    for item in execution.inputs.diagnostics
                ],
            }
            write_json(root / PYTHON_ACCEPTANCE, report)
        for profile in STRATEGY_PROFILES:
            report["profiles"].setdefault(
                profile, {"status": NOT_RUN, "reason": "prior_dependency_failure"}
            )
        report["calendar_after"] = coverage_snapshot()
        report["preflight_after"] = asdict(service.preflight(request))
        status = overall_status(item["status"] for item in report["profiles"].values())
        report["status"] = status
        if status == PASS:
            report["same_input"] = (
                len({item["fingerprint"] for item in report["profiles"].values()}) == 1
            )
            assert report["same_input"], "public_inputs_changed_between_profiles"
        write_json(root / PYTHON_ACCEPTANCE, report)
        return status
    except (FuturesRollError, AssertionError) as exc:
        return fail_report(report, root, exc)
    except Exception as exc:
        # The gate must fail closed: an unexpected error may never leave a prior PASS.
        return fail_report(report, root, exc)


def reproduce(root: Path) -> str:
    report = new_report("offline_evidence_reproduction")
    # Invalidate any earlier PASS before verification starts.
    write_json(root / REPRODUCTION_ACCEPTANCE, report)
    (root / "reproduction.json").unlink(missing_ok=True)
    acceptance = read_json(root / PYTHON_ACCEPTANCE)
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("status") != PASS
        or acceptance.get("same_input") is not True
    ):
        report["status"] = NOT_RUN
        report["reason"] = "real_acceptance_not_passed"
        for profile in STRATEGY_PROFILES:
            report["profiles"][profile] = {
                "status": NOT_RUN,
                "reason": "real_acceptance_not_passed",
            }
        write_json(root / REPRODUCTION_ACCEPTANCE, report)
        return NOT_RUN
    report["acceptance_run_id"] = acceptance.get("run_id")
    expected_profiles = acceptance.get("profiles")
    if not isinstance(expected_profiles, dict):
        expected_profiles = {}
    for profile in STRATEGY_PROFILES:
        evidence_path = root / f"{profile}-evidence.json"
        result_path = root / f"{profile}-result.json"
        expected = expected_profiles.get(profile)
        if not evidence_path.is_file() or not result_path.is_file():
            report["profiles"][profile] = {"status": NOT_RUN, "reason": "missing_evidence"}
            continue
        if not isinstance(expected, dict) or expected.get("status") != PASS:
            report["profiles"][profile] = {
                "status": NOT_RUN,
                "reason": "real_acceptance_not_passed",
            }
            continue
        started = time.monotonic()
        try:
            verified = reproduce_futures_roll_evidence(evidence_path.read_bytes())
            expected_result = read_json(result_path)
            assert (
                json.loads(json.dumps(asdict(verified.result), default=str)) == expected_result
            )
            assert verified.status == "verified"
            assert expected.get("fingerprint") == verified.input_fingerprint
        except (FuturesRollError, AssertionError, OSError) as exc:
            report["profiles"][profile] = {
                "status": FAIL,
                "reason": exc.reason if isinstance(exc, FuturesRollError) else "evidence_mismatch",
            }
            continue
        report["profiles"][profile] = {
            "status": PASS,
            "reproduction": verified.status,
            "fingerprint": verified.input_fingerprint,
            "events": verified.state_event_count,
            "seconds": time.monotonic() - started,
        }
    status = overall_status(item["status"] for item in report["profiles"].values())
    report["status"] = status
    write_json(root / REPRODUCTION_ACCEPTANCE, report)
    return status


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--mode", choices=("python", "serve", "reproduce"), required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not args.root.is_absolute() or root.is_relative_to(REPO_ROOT):
        parser.error("root must be an absolute artifact directory outside the repository")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.mode == "reproduce":
        status = reproduce(root)
        print(json.dumps({"phase": "reproduce_finished", "status": status}), flush=True)
        return exit_code(status)
    with isolated_cache(root):
        if args.mode == "python":
            status = accept_python(root)
            print(json.dumps({"phase": "python_finished", "status": status}), flush=True)
            return exit_code(status)
        import uvicorn

        from ui_http.app import create_app

        uvicorn.run(create_app(), host="127.0.0.1", port=8011, proxy_headers=False)
        return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
