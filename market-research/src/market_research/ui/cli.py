"""Canonical human-facing CLI for retained Research Studies."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from datetime import date
from typing import Never

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryError,
    CSI1000IMBasisHistoryRequest,
)

from ..shared.im_basis import ResearchInputError
from ..studies.im_annualized_basis_baseline import BaselineStudyError
from ..studies.im_basis_forward_return_association import AssociationStudyError
from . import catalog, configuration
from .execution import ResearchOutputError, canonical_run_directory, execute_run

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class ResearchArgumentParser(argparse.ArgumentParser):
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


def command_list() -> int:
    for entry in catalog.CATALOG:
        print(entry.study_id)
        print(f"    {entry.description}")
    return 0


def command_config() -> int:
    try:
        research_config = configuration.load_config()
    except configuration.ResearchConfigError as exc:
        return _failure("Configuration error", str(exc), 3)
    print(f"Config source: {research_config.source}")
    print(f"Output root:   {research_config.output_root}")
    return 0


def command_run(study_id: str, start: str, end: str, *, overwrite: bool) -> int:
    entry = catalog.find_study(study_id)
    if entry is None:
        supported = ", ".join(item.study_id for item in catalog.CATALOG)
        return _failure("Input error", f"unknown study ID {study_id!r}; supported: {supported}", 2)
    if not _valid_date(start) or not _valid_date(end):
        return _failure("Input error", "--start and --end must use valid YYYY-MM-DD dates", 2)
    if start > end:
        return _failure("Input error", "--start must be on or before --end", 2)

    try:
        research_config = configuration.load_config()
    except configuration.ResearchConfigError as exc:
        return _failure("Configuration error", str(exc), 3)

    request = CSI1000IMBasisHistoryRequest(start_trade_date=start, end_trade_date=end)
    run_directory = canonical_run_directory(
        research_config.output_root, entry.study_id, start, end
    )
    try:
        artifacts = execute_run(entry, request, run_directory, overwrite=overwrite)
    except CSI1000IMBasisHistoryError as exc:
        return _failure("Snapshot/data error", str(exc), 4)
    except (ResearchInputError, BaselineStudyError, AssociationStudyError) as exc:
        return _failure("Study/sample error", str(exc), 5)
    except ResearchOutputError as exc:
        return _failure("Output error", str(exc), 6)

    print("Study completed")
    print()
    print(f"Study:       {entry.study_id}")
    print(f"Date range:  {start} → {end}")
    print(f"Output:      {run_directory}")
    print()
    print("Artifacts:")
    for artifact in artifacts:
        print(f"  {artifact.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = ResearchArgumentParser(
        prog="market-research", description="Run retained market Research Studies."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List runnable retained Studies.")
    subparsers.add_parser("config", help="Show the resolved Research configuration.")
    run_parser = subparsers.add_parser("run", help="Run and retain one Study.")
    run_parser.add_argument("study_id", help="Stable Study ID from 'market-research list'.")
    run_parser.add_argument("--start", required=True, metavar="YYYY-MM-DD")
    run_parser.add_argument("--end", required=True, metavar="YYYY-MM-DD")
    run_parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list":
        return command_list()
    if args.command == "config":
        return command_config()
    return command_run(args.study_id, args.start, args.end, overwrite=args.overwrite)
