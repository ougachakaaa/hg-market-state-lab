"""Opt-in WP4 verification of retained real inputs; never acquires Source facts.

Run from repository root:
poetry run python market_backtesting/tests/real_result_acceptance.py --retained-root PATH
Only the existing acceptance harness redirects Dataset storage for public export.
"""

import argparse
import importlib
import json
import os
import subprocess
import tempfile
from dataclasses import asdict
from datetime import date
from pathlib import Path
from unittest.mock import patch

from data_lake import OperationError
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service
from market_backtesting.cases.futures_roll_long import (
    STRATEGY_PROFILES,
    FuturesRollError,
    FuturesRollExecution,
    FuturesRollRequest,
    PreparedFuturesRollInputs,
    analyze_futures_roll,
    build_backtest_result,
    build_evidence_package,
    encode_evidence_package,
    replay_futures_roll,
    reproduce_futures_roll_evidence,
)
from market_backtesting.cases.futures_roll_long.evidence import _json
from market_backtesting.cases.futures_roll_long.fingerprint import (
    decode_canonical_inputs,
    input_fingerprint,
)
from market_backtesting.cases.futures_roll_long.public_inputs import (
    build_replay_input,
    public_requests_for,
    validate_retained_exports,
)

FINGERPRINT = "0ff0446fa3f534139dc1c1d4ed3c1667fce68821e9670aa9a7116f96c9022e7b"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-root", type=Path, required=True)
    args = parser.parse_args()
    output = Path(tempfile.mkdtemp(prefix="w2-wp4-real-im-"))
    report = {"status": "NOT RUN", "profiles": {}, "source_acquisition": False}
    fixtures = {}
    try:
        exports = decode_canonical_inputs(
            (args.retained_root / "canonical-inputs.json").read_bytes()
        )
        fingerprint = input_fingerprint(exports)
        if fingerprint != FINGERPRINT:
            raise AssertionError("retained_fingerprint_mismatch")
        composition = importlib.import_module(
            "data_lake.datasets.tushare_trade_calendar._composition"
        )
        with patch.object(
            composition,
            "database_path",
            lambda identity, *_: args.retained_root / "cache" / f"{identity}.sqlite3",
        ):
            auxiliary = create_service().export(
                TradeCalendarRange("SSE", date(2025, 2, 17), date(2025, 3, 24))
            )
        for profile, total in zip(
            STRATEGY_PROFILES, (31360.00000000003, 32080.000000000102), strict=True
        ):
            request = FuturesRollRequest("IM", date(2025, 2, 17), date(2025, 3, 24), profile)
            validate_retained_exports(request, exports, auxiliary)
            public, sse = public_requests_for(request, exports)
            inputs = PreparedFuturesRollInputs(
                request,
                build_replay_input(request, exports, fingerprint),
                exports,
                public,
                (),
                fingerprint,
                sse,
                auxiliary,
            )
            replay = replay_futures_roll(inputs.replay_input)
            execution = FuturesRollExecution(
                request,
                replay.sessions[0],
                replay.sessions[-1],
                replay,
                analyze_futures_roll(replay),
                inputs,
            )
            result = build_backtest_result(execution)
            assert result.summary.total_pnl == total
            assert result.summary.benchmark_return == 0.012540726708617722
            assert result.window.cffex_session_count == 26
            assert replay.replay.final_portfolio.position is None
            assert result.rolls[0].old_contract_code == "IM2503.CFX"
            assert result.rolls[0].new_contract_code == (
                "IM2504.CFX" if "M1" in profile else "IM2506.CFX"
            )
            payload = encode_evidence_package(build_evidence_package(execution, result))
            verified = reproduce_futures_roll_evidence(payload, result)
            assert verified.status == "verified"
            (output / f"{profile}-evidence.json").write_bytes(payload)
            (output / f"{profile}-result.json").write_bytes(_json(asdict(result)))
            for name in ("returns", "drawdown"):
                fixtures[f"{profile}-{name}"] = asdict(getattr(result.views, name))
            report["profiles"][profile] = {  # type: ignore[index]
                "status": "PASS",
                "summary": asdict(result.summary),
                "fingerprint": fingerprint,
                "sessions": len(result.daily),
                "events": verified.state_event_count,
                "final_flat": True,
                "offline_reproduction": "PASS",
            }
        fixture = output / "views.json"
        fixture.write_bytes(_json(fixtures))
        root = Path(__file__).resolve().parents[2]
        check = subprocess.run(
            [
                "node_modules/.bin/vitest",
                "run",
                "--config",
                "../market_backtesting/tests/v2_contract.vitest.mjs",
            ],
            cwd=root / "ui_web",
            env={**os.environ, "W2_V2_FIXTURE": str(fixture)},
            capture_output=True,
            text=True,
        )
        (output / "v2-conformance.txt").write_text(check.stdout + check.stderr)
        assert check.returncode == 0, "frontend_v2_conformance_failed"
        report["status"] = "PASS"
        report["v2_conformance"] = "PASS"
    except (OSError, OperationError):
        report["reason"] = "retained_public_inputs_unavailable"
    except (AssertionError, FuturesRollError) as exc:
        report["status"] = "FAIL"
        report["reason"] = "retained_evidence_verification_failed"
        report["verification_reason"] = (
            exc.reason if isinstance(exc, FuturesRollError) else "oracle_assertion_failed"
        )
    (output / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"artifact": str(output), **report}))
    if report["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
