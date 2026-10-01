"""Study-local CLI for the MO Option Risk Premium Baseline."""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Never

from market_snapshot.products import index_daily_history as index_product
from market_snapshot.products.index_daily_history import IndexDailyHistoryError
from market_snapshot.products.mo_option_chain import service as chain_product

from ...ui import configuration
from ...ui.execution import ResearchOutputError, canonical_run_directory, execute_run
from . import evidence, observations, study
from .study import MOOptionRiskPremiumRequest, MOOptionRiskPremiumStudyError, SnapshotContractError

STUDY_ID = study.STUDY_ID


class StudyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"Input error: {message}\n")


def _failure(category: str, message: str, code: int) -> int:
    print(f"{category}: {message}", file=sys.stderr)
    return code


def _dtes(raw: str) -> tuple[int, ...]:
    parts = [part.strip() for part in raw.split(",")]
    if any(re.fullmatch(r"[0-9]+", part) is None for part in parts):
        raise MOOptionRiskPremiumStudyError(
            "--dte-targets needs comma-separated positive integers."
        )
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise MOOptionRiskPremiumStudyError(
            "--dte-targets needs comma-separated positive integers."
        ) from exc


def _moneyness(raw: str) -> tuple[Decimal, ...]:
    try:
        return tuple(Decimal(x.strip()) for x in raw.split(","))
    except Exception as exc:
        raise MOOptionRiskPremiumStudyError(
            "--moneyness-targets needs comma-separated finite decimals >= 0."
        ) from exc


def _request(args: argparse.Namespace) -> MOOptionRiskPremiumRequest:
    return MOOptionRiskPremiumRequest(
        args.start_expiry,
        args.end_expiry,
        _dtes(args.dte_targets),
        _moneyness(args.moneyness_targets),
    )


def _execute(
    request: MOOptionRiskPremiumRequest,
    output_dir: Path,
    *,
    resume_source: bool = False,
) -> tuple[Path, ...]:
    started = time.monotonic()
    index_query = study.index_request(request)
    index = index_product.run_index_daily_history(index_query)
    observations._validate_index(index_query, index)
    dates = tuple(row.trade_date for row in index.sample_observations)
    chains: dict[str, tuple[chain_product.OptionChain, chain_product.OptionChain]] = {}
    kinds = (chain_product.PriceType.HIGH, chain_product.PriceType.LOW)
    with chain_product.open_chain_session(dates, resume=resume_source) as session:
        for completed, (date, results) in enumerate(session.iter_dates(kinds), start=1):
            pair: list[chain_product.OptionChain] = []
            for kind in kinds:
                read = results[kind]
                if read.error is not None:
                    raise SnapshotContractError(f"MO Chain {date} {kind.value}: {read.error}")
                if read.chain is None:
                    raise SnapshotContractError(f"MO Chain {date} {kind.value} returned no chain.")
                pair.append(read.chain)
            chains[date] = pair[0], pair[1]
            attempts = session.metrics()["attempts"] + 1
            print(
                f"Acquired {completed}/{len(dates)} dates; latest {date}; "
                f"elapsed {time.monotonic() - started:.1f}s; Source attempts {attempts}",
                flush=True,
            )
        if len(chains) != len(dates):
            raise SnapshotContractError("MO acquisition stopped before all dates completed.")
        acquisition = session.provenance()
    result = study.compute(request, index, chains)
    result.provenance["acquisition"] = acquisition
    return evidence.retain(result, output_dir)


def run(
    request: MOOptionRiskPremiumRequest,
    *,
    overwrite: bool,
    resume_source: bool = False,
) -> int:
    try:
        config = configuration.load_config()
    except configuration.ResearchConfigError as exc:
        return _failure("Configuration error", str(exc), 3)
    try:
        directory = canonical_run_directory(config.output_root, STUDY_ID, study.run_key(request))
        artifacts = execute_run(
            lambda staging: _execute(request, staging, resume_source=resume_source),
            directory,
            overwrite=overwrite,
        )
    except IndexDailyHistoryError as exc:
        return _failure("Snapshot/data error", str(exc), 4)
    except chain_product.ChainReadError as exc:
        return _failure("Snapshot/data error", str(exc), 4)
    except SnapshotContractError as exc:
        return _failure("Snapshot/data error", str(exc), 4)
    except MOOptionRiskPremiumStudyError as exc:
        return _failure("Study/sample error", str(exc), 5)
    except ResearchOutputError as exc:
        return _failure("Output error", str(exc), 6)
    print("Study completed")
    print(f"Study: {STUDY_ID}")
    print(f"Output: {directory}")
    print("Artifacts:")
    for path in artifacts:
        print(f"  {path.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = StudyArgumentParser(
        prog=f"lab research run {STUDY_ID}",
        description="Run and retain the MO Option Risk Premium Baseline Study.",
    )
    parser.add_argument("--start-expiry", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--end-expiry", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--dte-targets", default="10,20,30,40,50,60", metavar="D1,D2,...")
    parser.add_argument("--moneyness-targets", default="0,0.05,0.10,0.15,0.20", metavar="M1,M2,...")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--resume-source",
        action="store_true",
        help="Reuse verified Snapshot acquisition checkpoints.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        request = _request(args)
    except MOOptionRiskPremiumStudyError as exc:
        return _failure("Input error", str(exc), 2)
    return run(request, overwrite=args.overwrite, resume_source=args.resume_source)


if __name__ == "__main__":
    raise SystemExit(main())
