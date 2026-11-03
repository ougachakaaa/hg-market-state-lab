"""Acquire the fixed CSI1000 scope in isolated storage; explicit live opt-in required."""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from data_lake.providers.tushare import TushareExecutor
from live_e2e_acceptance import ROOT, isolated_storage, public, require
from market_research.descriptive.cases.price_segmentation import (
    SegmentationRequest,
    construct_observations,
    prepare_inputs,
)
from segmentation_live_e2e import verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-calls", type=int, help="Optional explicit Provider call cap")
    args = parser.parse_args()
    if not args.live or (args.max_calls is not None and args.max_calls <= 0):
        parser.error("--live and a positive --max-calls if specified are required")
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("--output must be an empty directory")
    calls: Counter[str] = Counter()
    original = TushareExecutor.call
    budget_exhausted = False

    def counted(self: Any, endpoint: str, **kwargs: Any) -> Any:
        nonlocal budget_exhausted
        if args.max_calls is not None and sum(calls.values()) >= args.max_calls:
            budget_exhausted = True
            raise RuntimeError("Provider call budget exceeded")
        calls[endpoint] += 1
        return original(self, endpoint, **kwargs)

    report: dict[str, Any] = {"verdict": "BLOCKED", "max_calls": args.max_calls}
    try:
        require(Path(sys.prefix) == ROOT / ".venv", "Root Poetry environment required")
        with TemporaryDirectory(prefix="segmentation-g6-") as tmp:
            with (
                isolated_storage(Path(tmp)) as audit,
                patch.object(TushareExecutor, "call", counted),
            ):
                request = SegmentationRequest(
                    "000852.SH", date(2020, 1, 1), date(2026, 10, 31), 0.01
                )
                prepared = prepare_inputs(request)
                verify(construct_observations(request, prepared))
                evidence = {
                    "request": public(request),
                    "input_fingerprint": prepared.input_fingerprint,
                    "input_evidence": public(prepared.input_provenance),
                }
                (args.output / "input_evidence.json").write_text(
                    json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                report.update(
                    verdict="PASS",
                    fingerprint=prepared.input_fingerprint,
                    sessions=prepared.input_point_count,
                )
            report["isolation"] = audit
    except Exception as exc:
        category = getattr(exc, "category", None)
        report["verdict"] = (
            "BLOCKED"
            if budget_exhausted
            or category
            in {"incomplete_calendar", "incomplete_price_series", "upstream_operation_failure"}
            else "FAIL"
        )
        report["failure"] = {
            "type": type(exc).__name__,
            "category": "provider_budget_exceeded" if budget_exhausted else category,
            "stage": getattr(exc, "stage", None),
        }
        if hasattr(exc, "evidence"):
            report["input_evidence"] = public(exc.evidence)
    finally:
        report["provider_calls"] = dict(calls)
        (args.output / "acquisition_status.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(
        json.dumps({k: v for k, v in report.items() if k != "input_evidence"}, ensure_ascii=False)
    )
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
