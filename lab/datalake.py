"""DataLake public-service delegation and JSON file delivery."""

import argparse
import json
import re
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import cast

from data_lake import InvalidRequestError, OperationError
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service

DATASET = "tushare_trade_calendar"


def strict_date(value: str) -> date:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must be a valid YYYY-MM-DD") from exc


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("datalake", help="Use DataLake Dataset services.")
    operations = parser.add_subparsers(dest="datalake_command", required=True)
    operations.add_parser("list", help="List supported Dataset IDs.")
    for operation in ("coverage", "ensure", "export"):
        command = operations.add_parser(
            operation, help=f"{operation.title()} cached Dataset facts."
        )
        command.add_argument("dataset_id", choices=[DATASET])
        command.add_argument("--exchange", required=True)
        command.add_argument("--start-date", required=True, type=strict_date)
        command.add_argument("--end-date", required=True, type=strict_date)
        if operation == "export":
            command.add_argument("--output", required=True, type=Path)


def _json_date(value: object) -> str:
    if type(value) is date:
        return value.isoformat()
    raise TypeError("Unsupported export value")


def run(args: argparse.Namespace) -> int:
    if args.datalake_command == "list":
        print(DATASET)
        return 0
    try:
        request = TradeCalendarRange(args.exchange, args.start_date, args.end_date)
        service = create_service()
        if args.datalake_command == "coverage":
            print(f"Coverage: {asdict(service.coverage(request))}")
            return 0
        if args.datalake_command == "ensure":
            result = service.ensure(request)
            summary = asdict(result)
            summary.pop("failures")
            print(f"Ensure: {summary}")
            for failure in result.failures:
                exchange, cal_date = cast(tuple[str, date], failure.identity)
                print(f"Failed {exchange} {cal_date}: {failure.reason}")
            if not result.complete:
                print("Target coverage remains incomplete")
            return 0 if result.complete else 1
        view = service.export(request)
        payload = json.dumps(asdict(view), default=_json_date, ensure_ascii=False, indent=2)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Exported {len(view.records)} records to {args.output}")
        print(f"Coverage: {asdict(view.coverage)}")
        return 0
    except InvalidRequestError as exc:
        print(f"Invalid request: {exc}", file=sys.stderr)
        return 2
    except OperationError as exc:
        print(f"Operation failed: {exc}", file=sys.stderr)
        return 1
    except (OSError, TypeError, ValueError):
        print("Export file could not be delivered", file=sys.stderr)
        return 1
