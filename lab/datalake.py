"""DataLake public-service delegation and JSON file delivery."""

import argparse
import json
import logging
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, cast

from data_lake import InvalidRequestError, OperationError
from data_lake.datasets import tushare_equity_index_futures as futures
from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_index_daily as index
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service

DATASET = "tushare_trade_calendar"
DATASETS = (
    DATASET,
    "tushare_index_daily",
    "tushare_equity_index_futures",
    "tushare_equity_index_options",
)


def strict_date(value: str) -> date:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must be a valid YYYY-MM-DD") from exc


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("datalake", help="Use DataLake Dataset services.")
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="DataLake stderr/file log detail.",
    )
    parser.add_argument("--log-file", type=Path, help="Optional UTF-8 diagnostic log file.")
    operations = parser.add_subparsers(dest="datalake_command", required=True)
    operations.add_parser("list", help="List supported Dataset IDs.")
    for operation in ("coverage", "ensure", "export"):
        command = operations.add_parser(
            operation, help=f"{operation.title()} cached Dataset facts."
        )
        datasets = command.add_subparsers(dest="dataset_id", required=True)
        for dataset in DATASETS:
            target = datasets.add_parser(dataset, help=f"Use {dataset} public service.")
            if dataset == DATASET:
                target.add_argument("--exchange", required=True)
            elif dataset == "tushare_index_daily":
                target.add_argument("--index-codes", required=True, nargs="+")
            else:
                target.add_argument("--product-codes", required=True, nargs="+")
            target.add_argument("--start-date", required=True, type=strict_date)
            target.add_argument("--end-date", required=True, type=strict_date)
            if operation == "export":
                target.add_argument("--output", required=True, type=Path)


def _json_date(value: object) -> str:
    if type(value) is date:
        return value.isoformat()
    raise TypeError("Unsupported export value")


@contextmanager
def _logging(args: argparse.Namespace) -> Iterator[None]:
    logger = logging.getLogger("data_lake")
    old = logger.handlers[:], logger.level, logger.propagate
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    try:
        if getattr(args, "log_file", None) is not None:
            handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        for handler in handlers:
            handler.setFormatter(formatter)
        logger.handlers = handlers
        logger.setLevel(getattr(args, "log_level", "INFO"))
        logger.propagate = False
        yield
    finally:
        logger.handlers, logger.level, logger.propagate = old
        for handler in handlers:
            handler.close()


def run(args: argparse.Namespace) -> int:
    try:
        with _logging(args):
            return _run(args)
    except OSError:
        print("Diagnostic log file could not be opened", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace) -> int:
    if args.datalake_command == "list":
        print("\n".join(DATASETS))
        return 0
    try:
        request: Any
        service: Any
        if args.dataset_id == DATASET:
            request = TradeCalendarRange(args.exchange, args.start_date, args.end_date)
            service = create_service()
        elif args.dataset_id == "tushare_index_daily":
            request = index.IndexDailyRange(args.index_codes, args.start_date, args.end_date)
            service = index.create_service()
        elif args.dataset_id == "tushare_equity_index_futures":
            request = futures.FuturesDailyRange(args.product_codes, args.start_date, args.end_date)
            service = futures.create_service()
        else:
            request = options.OptionsDailyRange(args.product_codes, args.start_date, args.end_date)
            service = options.create_service()
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
