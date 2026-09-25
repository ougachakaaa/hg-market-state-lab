"""CLI over the Data Service catalog (semantic name ``dms``).

Authority: ``services/delivery.md`` sections 4 and 5.

Semantics:

    dms list
    dms get <service_id> --date YYYY-MM-DD

The CLI only parses arguments, validates CLI-level input, resolves a Data Service
and reports its result or error. Which Captures a service needs, in what order
they run, which Source endpoint each one calls and what the Analysis Preparation
derives are all owned by the Data Service (``ARCHITECTURE.md`` 2).

Implementation surface (the repository stays Poetry ``package-mode = false``):

    poetry run python scripts/dms.py list
    poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .services import DataServiceError, catalog
from .sources import tushare


def report_failure(service_id: str, target_trade_date: str, message: str) -> None:
    """Report a failed Data Service request on stderr."""
    print(f"service={service_id} date={target_trade_date} {message}", file=sys.stderr)


def command_list() -> int:
    """Print the catalog: ``service_id`` and description of each entry."""
    for service in catalog.CATALOG:
        print(f"{service.service_id}\t{service.description}")
    return 0


def command_get(service_id: str, target_trade_date: str) -> int:
    """Run one explicit Data Service request for one target trade date.

    The date must be an explicit ``YYYY-MM-DD`` target trade date; there is no
    ``today`` / ``latest`` / fallback behaviour. An unsupported service or an
    invalid date fails before any Source execution.
    """
    service = catalog.find_service(service_id)
    if service is None:
        supported = ", ".join(entry.service_id for entry in catalog.CATALOG)
        report_failure(service_id, target_trade_date, f"unknown service_id; supported: {supported}")
        return 2
    if not tushare.is_iso_date(target_trade_date):
        report_failure(
            service_id,
            target_trade_date,
            "invalid date; --date must be an explicit YYYY-MM-DD target_trade_date",
        )
        return 2

    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        output_path = service.run(api, target_trade_date)
    except (tushare.TushareSourceError, DataServiceError) as exc:
        report_failure(service_id, target_trade_date, f"error={exc}")
        return 1

    print(
        json.dumps(
            {
                "service": service.service_id,
                "target_trade_date": target_trade_date,
                "output_path": str(output_path),
            }
        )
    )
    return 0


def command_for(args: argparse.Namespace) -> int:
    """Dispatch one parsed command."""
    if args.command == "list":
        return command_list()
    return command_get(args.service_id, args.target_trade_date)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dms", description="Request a Data Service for an explicit target trade date."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List the supported Data Services.")

    get_parser = subparsers.add_parser("get", help="Request one Data Service for one date.")
    get_parser.add_argument("service_id", help="Data Service id, as printed by 'dms list'.")
    get_parser.add_argument(
        "--date",
        required=True,
        dest="target_trade_date",
        metavar="YYYY-MM-DD",
        help="Explicit target_trade_date; no today / latest / fallback.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    return command_for(build_parser().parse_args(argv))
