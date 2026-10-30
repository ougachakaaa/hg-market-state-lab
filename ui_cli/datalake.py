"""DataLake public-service delegation and JSON file delivery."""

import argparse
import json
import logging
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, fields, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

from data_lake import InvalidRequestError, OperationError
from data_lake.datasets import tushare_equity_index_futures as futures
from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_index_daily as index
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service

from .datalake_parser import DATASET, DATASETS


def _json_date(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: getattr(value, field.name) for field in fields(value)}
    if type(value) is date:
        return value.isoformat()
    raise TypeError("Unsupported export value")


def _deliver(view: object, output: Path) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            chunks: list[str] = []
            size = 0
            encoder = json.JSONEncoder(default=_json_date, ensure_ascii=False, indent=2)
            for chunk in encoder.iterencode(view):
                chunks.append(chunk)
                size += len(chunk)
                if size >= 1024 * 1024:
                    stream.write("".join(chunks))
                    chunks.clear()
                    size = 0
            if chunks:
                stream.write("".join(chunks))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


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
        _deliver(view, args.output)
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
