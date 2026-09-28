"""Study-local CLI for Price-to-Lagged-MA Short-Horizon Reversion."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Never

from market_snapshot.products import index_daily_history as snapshot_product
from market_snapshot.products.index_daily_history import IndexDailyHistoryError

from ...shared.distribution import DistributionInputError
from ...ui import configuration
from ...ui.execution import ResearchOutputError, canonical_run_directory, execute_run
from . import study
from .study import ReversionRequest, ReversionStudyError

STUDY_ID = study.STUDY_ID


class StudyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"Input error: {message}\n")


def _failure(category: str, message: str, exit_code: int) -> int:
    print(f"{category}: {message}", file=sys.stderr)
    return exit_code


def _edges(raw: str) -> tuple[Decimal, ...]:
    try:
        return tuple(Decimal(part) for part in raw.split(","))
    except InvalidOperation as exc:
        raise ReversionStudyError("--bucket-edges must be comma-separated decimal ratios.") from exc


def _horizons(raw: str) -> tuple[int, ...]:
    parts = raw.split(",")
    if not parts or any(not part or not part.isascii() or not part.isdecimal() for part in parts):
        raise ReversionStudyError("--horizons must be comma-separated positive integers.")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ReversionStudyError("--horizons must be comma-separated positive integers.") from exc


def _request(args: argparse.Namespace) -> ReversionRequest:
    if not args.window.isascii() or not args.window.isdecimal():
        raise ReversionStudyError("--window must be a positive integer.")
    try:
        window = int(args.window)
    except ValueError as exc:
        raise ReversionStudyError("--window must be a positive integer.") from exc
    return ReversionRequest(
        instrument=args.instrument,
        sample_start_trade_date=args.start,
        sample_end_trade_date=args.end,
        reference_method=args.method,
        reference_window=window,
        percentile_bucket_edges=_edges(args.bucket_edges),
        forward_horizons=_horizons(args.horizons),
    )


def _execute(request: ReversionRequest, output_dir: Path) -> tuple[Path, ...]:
    snapshot = snapshot_product.run_index_daily_history(study.derive_snapshot_request(request))
    result = study.compute(request, snapshot)
    return study.retain(result, snapshot, output_dir)


def run(request: ReversionRequest, *, overwrite: bool) -> int:
    try:
        research_config = configuration.load_config()
    except configuration.ResearchConfigError as exc:
        return _failure("Configuration error", str(exc), 3)
    try:
        run_directory = canonical_run_directory(
            research_config.output_root, STUDY_ID, study.run_key(request)
        )
        artifacts = execute_run(
            lambda output_dir: _execute(request, output_dir), run_directory, overwrite=overwrite
        )
    except IndexDailyHistoryError as exc:
        return _failure("Snapshot/data error", str(exc), 4)
    except (ReversionStudyError, DistributionInputError) as exc:
        return _failure("Study/sample error", str(exc), 5)
    except ResearchOutputError as exc:
        return _failure("Output error", str(exc), 6)
    print("Study completed")
    print(f"Study:  {STUDY_ID}")
    print(f"Output: {run_directory}")
    for artifact in artifacts:
        print(f"  {artifact.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StudyArgumentParser(
        prog=f"lab research run {STUDY_ID}",
        description="Run and retain the Price-to-Lagged-MA Short-Horizon Reversion Study.",
    )
    parser.add_argument("--instrument", required=True, metavar="TS_CODE")
    parser.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--method", choices=("sma", "volume_weighted"), default="sma")
    parser.add_argument("--window", default="60", metavar="N")
    parser.add_argument(
        "--bucket-edges", default=",".join(study.DEFAULT_EDGES), metavar="P0,P1,..."
    )
    parser.add_argument("--horizons", default="1,3,5", metavar="H1,H2,...")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        request = _request(args)
    except ReversionStudyError as exc:
        return _failure("Input error", str(exc), 2)
    return run(request, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
