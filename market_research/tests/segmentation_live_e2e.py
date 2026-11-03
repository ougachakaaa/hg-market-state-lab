"""Explicit isolated Price Segmentation live gate. Never run as part of pytest."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import UTC, date, datetime
from math import isfinite, log
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from data_lake import OperationError
from data_lake.providers.tushare import TushareExecutor
from data_lake.providers.tushare._executor import request_interval, resolve_credential
from live_e2e_acceptance import ROOT, IsolationError, isolated_storage, public, require
from market_research.descriptive.cases.price_segmentation import (
    InputPreparationError,
    SegmentationRequest,
    observe_price_segments,
)


def verify(result: Any) -> dict[str, Any]:
    """Independently check final public facts and all financial/numerical outputs."""
    prepared = result.provenance
    request = result.request_identity
    cal, idx = (a.final_export for a in prepared.input_provenance)
    require(cal is not None and idx is not None, "Final exports exist")
    for view in (cal, idx):
        cov = view.coverage
        require(cov.complete and cov.requested_units == cov.successful_units, "Coverage complete")
        require(cov.missing_units == cov.pending_units == cov.failed_units == 0, "No missing units")
    require(cal.scope == ("SSE",), "SSE calendar")
    require(
        [r.cal_date.toordinal() for r in cal.records]
        == list(range(request.start_date.toordinal(), request.end_date.toordinal() + 1)),
        "All calendar dates",
    )
    require(all(r.exchange == "SSE" and r.is_open in (0, 1) for r in cal.records), "Calendar rows")
    sessions = tuple(r.cal_date for r in cal.records if r.is_open == 1)
    rows = idx.records
    require(len(rows) == len(sessions) == idx.coverage.requested_units, "Every session priced")
    require(
        tuple(r.trade_date for r in rows) == sessions == prepared.session_dates, "Exact sessions"
    )
    require(
        all(
            r.index_code == "000852.SH" and r.symbol == "000852" and r.name == "中证1000"
            for r in rows
        ),
        "CSI1000 public metadata",
    )
    closes = tuple(r.close for r in rows)
    require(all(isfinite(c) and c > 0 for c in closes), "Positive finite prices")
    require(closes == prepared.closes, "Actual closes")
    logs = tuple(log(c) for c in closes)
    require(logs == prepared.log_prices, "Natural log")
    payload = [
        "price_segmentation_inputs_v1",
        "tushare_index_daily",
        "index_daily",
        1,
        request.index_code,
        [[d.isoformat(), c.hex()] for d, c in zip(sessions, closes, strict=True)],
    ]
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    require(digest == prepared.input_fingerprint, "Independent fingerprint")
    points = result.important_points
    indices = tuple(p.index for p in points)
    require(indices[0] == 0 and indices[-1] == len(rows) - 1, "Endpoints")
    require(all(a < b for a, b in zip(indices, indices[1:], strict=False)), "Ordered points")
    require(
        all((p.date, p.close) == (sessions[p.index], closes[p.index]) for p in points),
        "Original point facts",
    )
    segments = result.segments
    require(len(segments) == len(points) - 1, "Segment count")
    require(sum(s.duration_sessions for s in segments) == len(rows) - 1, "Duration coverage")
    maximum = 0.0
    for s, a, b in zip(segments, points[:-1], points[1:], strict=True):
        require(
            (s.start_index, s.start_date, s.start_close) == (a.index, a.date, a.close),
            "Start point",
        )
        require((s.end_index, s.end_date, s.end_close) == (b.index, b.date, b.close), "End point")
        require(s.segment_identity == (request, a.index, b.index), "Segment identity")
        require(s.duration_sessions == b.index - a.index, "Session duration")
        require(s.amplitude_ratio == b.close / a.close - 1, "Simple return")
        direction = "up" if b.close > a.close else "down" if b.close < a.close else "flat"
        require(s.direction == direction, "Direction")
        require(
            s.touches_start_boundary == (a.index == 0)
            and s.touches_end_boundary == (b.index == len(rows) - 1),
            "Boundary flags",
        )
        for i in range(a.index + 1, b.index):
            delta = logs[b.index] - logs[a.index]
            product = delta * float(i - a.index)
            fraction = product / float(b.index - a.index)
            reconstructed = logs[a.index] + fraction
            maximum = max(maximum, abs(logs[i] - reconstructed))
    diag = result.diagnostics
    require(
        (diag.input_point_count, diag.important_point_count, diag.segment_count)
        == (len(rows), len(points), len(segments)),
        "Counts",
    )
    require(
        diag.algorithm_id == request.algorithm_id and diag.epsilon == request.epsilon,
        "Algorithm parameters",
    )
    require(
        maximum == diag.max_reconstruction_error and maximum <= request.epsilon,
        "Independent reconstruction",
    )
    return {
        "request": public(request),
        "metadata": {
            "code": rows[0].index_code,
            "symbol": rows[0].symbol,
            "name": rows[0].name,
            "market": rows[0].market,
            "publisher": rows[0].publisher,
            "category": rows[0].category,
        },
        "calendar_coverage": public(cal.coverage),
        "index_coverage": public(idx.coverage),
        "input_fingerprint": digest,
        "input_evidence": public(prepared.input_provenance),
        "log_prices": public(logs),
        "diagnostics": public(diag),
        "important_points": public(points),
        "segments": public(segments),
        "independent_checks": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--long", action="store_true", help="Run longer scope only after short passes"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "verdict": "BLOCKED",
        "tested_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "root_poetry_environment": Path(sys.prefix) == ROOT / ".venv",
        "scenarios": [],
    }
    calls: Counter[str] = Counter()
    limit = 24
    original_call = TushareExecutor.call

    def bounded_call(self: Any, endpoint: str, **parameters: Any) -> Any:
        if sum(calls.values()) >= limit:
            raise RuntimeError("Acceptance Source call budget exhausted")
        calls[endpoint] += 1
        return original_call(self, endpoint, **parameters)

    try:
        with TemporaryDirectory(prefix="segmentation-live-e2e-") as temporary:
            with isolated_storage(Path(temporary)) as audit:
                report["isolation"] = audit
                if not args.live:
                    report["blocker"] = "Live Source I/O not requested"
                else:
                    require(report["root_poetry_environment"], "Root Poetry environment required")
                    credential = resolve_credential()
                    require(bool(credential.strip()), "Credential unavailable")
                    del credential
                    report["credential_available"] = True
                    report["configured_calls_per_minute"] = 60 / request_interval()
                    windows = [(date(2024, 1, 16), 0.005)]
                    if args.long:
                        windows.append((date(2024, 2, 29), 0.01))
                    with patch.object(TushareExecutor, "call", bounded_call):
                        for end, epsilon in windows:
                            if report["scenarios"]:
                                limit += 24
                            request = SegmentationRequest(
                                "000852.SH", date(2024, 1, 8), end, epsilon
                            )
                            before = sum(calls.values())
                            result = observe_price_segments(request)
                            checked = verify(result)
                            after_first = sum(calls.values())
                            repeat = observe_price_segments(request)
                            verify(repeat)
                            require(
                                sum(calls.values()) == after_first,
                                "Repeated execution fetched Source",
                            )
                            require(
                                (
                                    repeat.request_identity,
                                    repeat.provenance.input_fingerprint,
                                    repeat.important_points,
                                    repeat.segments,
                                    repeat.diagnostics,
                                )
                                == (
                                    result.request_identity,
                                    result.provenance.input_fingerprint,
                                    result.important_points,
                                    result.segments,
                                    result.diagnostics,
                                ),
                                "Reproducibility",
                            )
                            checked["source_calls"] = after_first - before
                            checked["repeat_source_calls"] = sum(calls.values()) - after_first
                            checked["reproducibility"] = "passed"
                            report["scenarios"].append(checked)
                    report["verdict"] = "PASS"
    except IsolationError:
        report["blocker"] = "Isolation not established or escaped"
    except InputPreparationError as exc:
        report["blocker"] = {
            "category": exc.category,
            "stage": exc.stage,
            "evidence_count": len(exc.evidence),
        }
    except OperationError:
        report["blocker"] = "Provider credential or runtime configuration unavailable at preflight"
    except AssertionError as exc:
        report["verdict"] = "FAIL"
        report["verification_error"] = str(exc)
    except Exception as exc:
        report["verdict"] = "FAIL"
        report["error_type"] = type(exc).__name__
    finally:
        report["provider_calls"] = dict(calls)
        args.output.write_text(
            json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "verdict": report["verdict"],
                "provider_calls": report["provider_calls"],
                "blocker": report.get("blocker"),
            },
            ensure_ascii=True,
        )
    )
    return 0 if report["verdict"] == "PASS" or not args.live else 1


if __name__ == "__main__":
    raise SystemExit(main())
