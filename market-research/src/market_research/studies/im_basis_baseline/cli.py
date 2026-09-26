"""Study-local CLI for the IM annualized basis baseline."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Never

from market_snapshot.products import csi1000_im_basis_history as snapshot_product
from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryError,
    CSI1000IMBasisHistoryRequest,
)

from ...shared.im_basis import ResearchInputError
from ...ui import configuration
from ...ui.execution import ResearchOutputError, canonical_run_directory, execute_run
from . import study
from .study import BaselineStudyError

STUDY_ID = "im-basis-baseline"
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class StudyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"Input error: {message}\n")


def _valid_date(value: str) -> bool:
    if ISO_DATE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _failure(category: str, message: str, exit_code: int) -> int:
    print(f"{category}: {message}", file=sys.stderr)
    return exit_code


def _execute(
    request: CSI1000IMBasisHistoryRequest, output_dir: Path
) -> tuple[Path, ...]:
    snapshot = snapshot_product.run_csi1000_im_basis_history(request)
    study.run_and_retain(snapshot, output_dir)
    return tuple(sorted(path for path in output_dir.iterdir() if path.is_file()))


def run(start: str, end: str, *, overwrite: bool) -> int:
    if not _valid_date(start) or not _valid_date(end):
        return _failure("Input error", "--start and --end must use valid YYYY-MM-DD dates", 2)
    if start > end:
        return _failure("Input error", "--start must be on or before --end", 2)

    try:
        research_config = configuration.load_config()
    except configuration.ResearchConfigError as error:
        return _failure("Configuration error", str(error), 3)

    request = CSI1000IMBasisHistoryRequest(start_trade_date=start, end_trade_date=end)
    run_directory = canonical_run_directory(
        research_config.output_root, STUDY_ID, start, end
    )

    def execute(output_dir: Path) -> tuple[Path, ...]:
        return _execute(request, output_dir)

    try:
        artifacts = execute_run(execute, run_directory, overwrite=overwrite)
    except CSI1000IMBasisHistoryError as error:
        return _failure("Snapshot/data error", str(error), 4)
    except (ResearchInputError, BaselineStudyError) as error:
        return _failure("Study/sample error", str(error), 5)
    except ResearchOutputError as error:
        return _failure("Output error", str(error), 6)

    print("Study completed")
    print()
    print(f"Study:       {STUDY_ID}")
    print(f"Date range:  {start} → {end}")
    print(f"Output:      {run_directory}")
    print()
    print("Artifacts:")
    for artifact in artifacts:
        print(f"  {artifact.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StudyArgumentParser(
        prog=f"dev.py research run {STUDY_ID}",
        description="Run and retain the IM annualized basis baseline Study.",
    )
    parser.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args.start, args.end, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
