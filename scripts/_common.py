"""Shared helpers for the Raw Dataset collectors.

This module only holds what the collectors genuinely need:

* reading the Tushare credential;
* date representation conversion;
* minimal normalization (DataFrame -> JSON-compatible records);
* writing Raw Dataset files;
* the Raw output roots, plus the two Source-fact filters and the source-date
  normalization that the collectors of the CSI1000 analysis scenario share.

It intentionally contains no architecture layer: no base data source, no
registry, no pipeline. See ``ARCHITECTURE.md`` sections 9 and 10.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Collection, Iterator, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
# Goal-scoped Raw root of guides/csi1000-5d-analysis-data.md section 7.
CSI1000_RAW_SUBDIR = "csi1000-5d-analysis"
ENV_FILE = REPO_ROOT / ".env"

TOKEN_ENV_VAR = "TUSHARE_TOKEN"

TRADE_DATE_FIELD = "trade_date"
TRADE_DATE_ISO_FORMAT = "%Y-%m-%d"
TRADE_DATE_TUSHARE_FORMAT = "%Y%m%d"
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

# Other Source date facts (contract lifecycle) that Raw records express in the
# same ``YYYY-MM-DD`` form as ``trade_date``.
SOURCE_DATE_FIELDS = ("list_date", "delist_date", "last_ddate")

# One Source row, ready to be serialized to JSON.
RawRecord = dict[str, Any]

# Signature of the Tushare call a collector needs, so tests can fake the Source.
QueryFunc = Callable[..., pd.DataFrame]


class CollectionError(Exception):
    """Raised when a Raw Dataset cannot be collected as the Guide requires."""


class TushareApi(Protocol):
    """The Tushare endpoints this project reads.

    ``tushare.pro.client.DataApi`` resolves endpoints dynamically and ships no
    type information, so only the endpoints actually used are described here.
    """

    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...

    def daily(self, *, trade_date: str) -> pd.DataFrame: ...

    def opt_basic(
        self, *, exchange: str, list_date: str | None = ..., fields: str | None = ...
    ) -> pd.DataFrame: ...

    def opt_daily(
        self,
        *,
        trade_date: str | None = ...,
        exchange: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...

    def fut_basic(
        self,
        *,
        exchange: str,
        fut_type: str | None = ...,
        fut_code: str | None = ...,
        fields: str | None = ...,
    ) -> pd.DataFrame: ...

    def fut_daily(
        self,
        *,
        ts_code: str | None = ...,
        trade_date: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...


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


def is_iso_date(value: Any) -> bool:
    """Report whether a value is already a valid ``YYYY-MM-DD`` date."""
    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        return False
    try:
        datetime.strptime(value, TRADE_DATE_ISO_FORMAT)
    except ValueError:
        return False
    return True


def to_iso_date_or_none(value: Any) -> str | None:
    """Convert an optional Source ``YYYYMMDD`` value to ``YYYY-MM-DD``.

    Contract lifecycle facts (``list_date`` / ``delist_date``) are optional in
    the Source, so missing values stay ``None`` instead of failing: the
    collectors treat such a contract as having no lifecycle bound on that side.
    A value that already uses the Raw form is kept as it is, so both a Source
    frame and an already-normalized Raw record give the same date.
    """
    if value is None or (isinstance(value, float) and value != value):
        return None
    if is_iso_date(value):
        return value
    text = str(value).strip()
    if not text:
        return None
    return to_iso_date(text)


def in_date_range(record: RawRecord, field: str, start: str, end: str) -> bool:
    """Report whether ``record[field]`` is an ISO date inside ``[start, end]``."""
    value = record.get(field)
    return isinstance(value, str) and start <= value <= end


def fetch_source_frames(
    query: QueryFunc, codes: Collection[str], **params: str
) -> Iterator[tuple[str, pd.DataFrame]]:
    """Call one Source endpoint per code, keeping the requested code alongside.

    Iterating a Source DataFrame must not be done by position: a DataFrame with
    duplicate index labels yields a Series instead of a row whenever a label
    repeats. Going through the requested code keeps the contract identity
    explicit and de-duplicated.
    """
    for code in sorted(codes):
        yield code, query(ts_code=code, **params)


def to_json_scalar(value: Any) -> Any:
    """Convert a numpy scalar to a JSON-compatible scalar; pass others through."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and value != value:  # NaN is not valid JSON.
        return None
    return value


def to_raw_records(frame: pd.DataFrame) -> list[RawRecord]:
    """Turn a Source DataFrame into Raw Dataset records (minimal normalization).

    Source fields are kept as-is; only Source date facts are expressed as
    ``YYYY-MM-DD`` (see ``SOURCE_DATE_FIELDS``) and numpy scalars become JSON
    scalars. Missing and already normalized date facts are kept as they are, so
    a Raw record that another Collector re-normalizes stays stable.
    """
    records: list[RawRecord] = []
    for row in frame.to_dict(orient="records"):
        record = {str(key): to_json_scalar(value) for key, value in row.items()}
        for field in (TRADE_DATE_FIELD, *SOURCE_DATE_FIELDS):
            iso_value = to_iso_date_or_none(record.get(field))
            if iso_value is not None:
                record[field] = iso_value
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
