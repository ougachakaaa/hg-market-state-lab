"""Shared helpers for the Raw Dataset collectors.

This module only holds what both collectors genuinely need:

* reading the Tushare credential;
* date representation conversion;
* minimal normalization (DataFrame -> JSON-compatible records);
* writing Raw Dataset files.

It intentionally contains no architecture layer: no base data source, no
registry, no pipeline. See ``ARCHITECTURE.md`` sections 9 and 10.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
ENV_FILE = REPO_ROOT / ".env"

TOKEN_ENV_VAR = "TUSHARE_TOKEN"

TRADE_DATE_FIELD = "trade_date"
TRADE_DATE_ISO_FORMAT = "%Y-%m-%d"
TRADE_DATE_TUSHARE_FORMAT = "%Y%m%d"
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

# One Source row, ready to be serialized to JSON.
RawRecord = dict[str, Any]

# Signature of the Tushare call a collector needs, so tests can fake the Source.
QueryFunc = Callable[..., pd.DataFrame]


class CollectionError(Exception):
    """Raised when a Raw Dataset cannot be collected as the Guide requires."""


class TushareApi(Protocol):
    """The Tushare endpoints this project reads.

    ``tushare.pro.client.DataApi`` resolves endpoints dynamically and ships no
    type information, so the two interfaces actually used are described here.
    """

    def index_daily(self, *, ts_code: str, trade_date: str) -> pd.DataFrame: ...

    def daily(self, *, trade_date: str) -> pd.DataFrame: ...


def get_tushare_token() -> str:
    """Return ``TUSHARE_TOKEN``, loading the local ``.env`` if present.

    Raises ``CollectionError`` instead of returning an empty token, so a
    missing credential fails before any Source request is made.
    """
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=False)

    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if not token:
        raise CollectionError(
            f"{TOKEN_ENV_VAR} is not set. Set it in the environment or in {ENV_FILE}."
        )
    return token


def create_tushare_api(token: str) -> TushareApi:
    """Create the Tushare API client for the given token."""
    import tushare as ts

    api: TushareApi = ts.pro_api(token)
    return api


def to_tushare_date(trade_date: str) -> str:
    """Convert a script-level ``YYYY-MM-DD`` date to Tushare ``YYYYMMDD``.

    The input must be exactly ``YYYY-MM-DD``; ``strptime`` alone would also
    accept forms such as ``2026-9-17``, which are not the script-level format
    defined in ``guides/daily-market-snapshot.md`` section 3.
    """
    if not ISO_DATE_PATTERN.fullmatch(trade_date):
        raise CollectionError(f"trade_date must use YYYY-MM-DD, got {trade_date!r}.")
    try:
        parsed = datetime.strptime(trade_date, TRADE_DATE_ISO_FORMAT)
    except ValueError as exc:
        raise CollectionError(f"trade_date is not a valid date: {trade_date!r}.") from exc
    return parsed.strftime(TRADE_DATE_TUSHARE_FORMAT)


def to_iso_date(trade_date: str) -> str:
    """Convert a Source ``YYYYMMDD`` date to ``YYYY-MM-DD``."""
    try:
        parsed = datetime.strptime(trade_date, TRADE_DATE_TUSHARE_FORMAT)
    except ValueError as exc:
        raise CollectionError(
            f"source {TRADE_DATE_FIELD} must use YYYYMMDD, got {trade_date!r}."
        ) from exc
    return parsed.strftime(TRADE_DATE_ISO_FORMAT)


def to_json_scalar(value: Any) -> Any:
    """Convert a numpy scalar to a JSON-compatible scalar; pass others through."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and value != value:  # NaN is not valid JSON.
        return None
    return value


def to_raw_records(frame: pd.DataFrame) -> list[RawRecord]:
    """Turn a Source DataFrame into Raw Dataset records (minimal normalization).

    Source fields are kept as-is; only ``trade_date`` is expressed as
    ``YYYY-MM-DD`` and numpy scalars become JSON scalars.
    """
    records: list[RawRecord] = []
    for row in frame.to_dict(orient="records"):
        record = {str(key): to_json_scalar(value) for key, value in row.items()}
        if TRADE_DATE_FIELD in record:
            record[TRADE_DATE_FIELD] = to_iso_date(str(record[TRADE_DATE_FIELD]))
        records.append(record)
    return records


def require_target_trade_date(records: Sequence[RawRecord], trade_date: str) -> None:
    """Ensure every collected row belongs to the requested trade date."""
    for record in records:
        if record.get(TRADE_DATE_FIELD) != trade_date:
            raise CollectionError(
                f"source returned {TRADE_DATE_FIELD}={record.get(TRADE_DATE_FIELD)!r} "
                f"for requested trade_date={trade_date}."
            )


def write_raw_dataset(records: Sequence[RawRecord], dataset_dir: Path, dataset: str) -> Path:
    """Write one Raw Dataset file and return its path."""
    dataset_dir.mkdir(parents=True, exist_ok=True)
    path = dataset_dir / f"{dataset}.json"
    path.write_text(json.dumps(list(records), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
