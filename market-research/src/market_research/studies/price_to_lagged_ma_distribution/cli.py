"""Study-local CLI for the Price-to-Lagged-MA Distribution."""

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
from .study import PriceToLaggedMARequest, PriceToLaggedMAStudyError

STUDY_ID = "price-to-lagged-ma-distribution"


class StudyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"Input error: {message}\n")


def _failure(category: str, message: str, exit_code: int) -> int:
    print(f"{category}: {message}", file=sys.stderr)
    return exit_code


def _percentiles(raw: str) -> tuple[Decimal, ...]:
    try:
        return tuple(Decimal(part) for part in raw.split(","))
    except InvalidOperation as exc:
        raise PriceToLaggedMAStudyError(
            "--percentiles must be comma-separated decimal probabilities."
        ) from exc


def _request(args: argparse.Namespace) -> PriceToLaggedMARequest:
    try:
        window = int(args.window)
    except ValueError as exc:
        raise PriceToLaggedMAStudyError("--window must be a positive integer.") from exc
    return PriceToLaggedMARequest(
        instrument=args.instrument,
        reference_window=window,
        reference_method=args.method,
        reference_method_parameters={},
        sample_start_trade_date=args.start,
        sample_end_trade_date=args.end,
        distribution_granularity=args.granularity,
        percentile_probabilities=_percentiles(args.percentiles),
    )


def _execute(request: PriceToLaggedMARequest, output_dir: Path) -> tuple[Path, ...]:
    snapshot = snapshot_product.run_index_daily_history(study.derive_snapshot_request(request))
    result = study.compute(request, snapshot)
    return study.retain(result, snapshot, output_dir)


def run(request: PriceToLaggedMARequest, *, overwrite: bool) -> int:
    try:
        research_config = configuration.load_config()
    except configuration.ResearchConfigError as error:
        return _failure("Configuration error", str(error), 3)

    def execute(output_dir: Path) -> tuple[Path, ...]:
        return _execute(request, output_dir)

    try:
        run_directory = canonical_run_directory(
            research_config.output_root, STUDY_ID, study.run_key(request)
        )
        artifacts = execute_run(execute, run_directory, overwrite=overwrite)
    except IndexDailyHistoryError as error:
        return _failure("Snapshot/data error", str(error), 4)
    except (PriceToLaggedMAStudyError, DistributionInputError) as error:
        return _failure("Study/sample error", str(error), 5)
    except ResearchOutputError as error:
        return _failure("Output error", str(error), 6)

    print("Study completed")
    print()
    print(f"Study:       {STUDY_ID}")
    print(f"Output:      {run_directory}")
    print()
    print("Artifacts:")
    for artifact in artifacts:
        print(f"  {artifact.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StudyArgumentParser(
        prog=f"dev.py research run {STUDY_ID}",
        description="Run and retain the Price-to-Lagged-MA Distribution Study.",
    )
    parser.add_argument("--instrument", required=True, metavar="TS_CODE")
    parser.add_argument("--window", required=True, metavar="N")
    parser.add_argument("--method", required=True, choices=("sma", "volume_weighted"))
    parser.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--granularity", required=True, metavar="RATIO")
    parser.add_argument("--percentiles", required=True, metavar="P1,P2,...")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        request = _request(args)
    except PriceToLaggedMAStudyError as error:
        return _failure("Input error", str(error), 2)
    return run(request, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
