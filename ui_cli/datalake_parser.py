"""DataLake argument definitions without loading market services or Providers."""

import argparse
import re
from datetime import date
from pathlib import Path

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
