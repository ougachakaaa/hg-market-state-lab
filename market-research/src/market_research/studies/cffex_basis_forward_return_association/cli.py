"""Study-local CLI for four-family CFFEX basis association evidence."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Never

from market_snapshot.products import cffex_equity_index_basis_history as snapshot_product
from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryError,
    CFFEXEquityIndexBasisHistoryRequest,
)

from ...ui import configuration
from ...ui.execution import ResearchOutputError, canonical_run_directory, execute_run
from . import study
from .study import CFFEXStudyError

STUDY_ID = "cffex-basis-forward-return-association"
FAMILIES = ("IF", "IH", "IC", "IM")


class StudyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"Input error: {message}\n")


def _valid_date(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _failure(category: str, message: str, code: int) -> int:
    print(f"{category}: {message}", file=sys.stderr)
    return code


def run(start: str, end: str, *, overwrite: bool) -> int:
    if not _valid_date(start) or not _valid_date(end) or start > end:
        return _failure(
            "Input error", "--start and --end must be ordered valid YYYY-MM-DD dates", 2
        )
    try:
        config = configuration.load_config()
    except configuration.ResearchConfigError as exc:
        return _failure("Configuration error", str(exc), 3)
    run_key = f"{start}__{end}"

    def execute(output_dir: Path) -> tuple[Path, ...]:
        snapshots = [
            snapshot_product.run_cffex_equity_index_basis_history(
                CFFEXEquityIndexBasisHistoryRequest(family, start, end)
            )
            for family in FAMILIES
        ]
        study.run_and_retain(snapshots, output_dir)
        return tuple(sorted(path for path in output_dir.iterdir() if path.is_file()))

    try:
        directory = canonical_run_directory(config.output_root, STUDY_ID, run_key)
        artifacts = execute_run(execute, directory, overwrite=overwrite)
    except CFFEXEquityIndexBasisHistoryError as exc:
        return _failure(f"Snapshot/data error ({exc.reason})", str(exc), 4)
    except CFFEXStudyError as exc:
        return _failure("Study/sample error", str(exc), 5)
    except ResearchOutputError as exc:
        return _failure("Output error", str(exc), 6)
    print(f"Study completed: {STUDY_ID}\nOutput: {directory}")
    for artifact in artifacts:
        print(f"  {artifact.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StudyArgumentParser(
        prog=f"lab research run {STUDY_ID}",
        description="Retain CFFEX equity-index basis/forward-return evidence.",
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
