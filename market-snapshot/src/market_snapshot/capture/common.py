"""Shared Source Capture helpers.

This module holds what the captures genuinely share:

* the Capture failure type and the Source-query signature;
* Raw record construction (minimal normalization of a Source frame);
* the Raw-representation date helpers the captures use on Source facts;
* the Source-fact filters of the CSI1000 analysis scenario captures.

It holds no endpoint binding and no analysis logic: concrete endpoint calls,
query parameters and Capture scope live in the individual ``capture`` modules,
and analyzer-specific transformation is not known here at all
(``ARCHITECTURE.md`` 2, 3).
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterator, Sequence
from typing import Any

import numpy as np
import pandas as pd

from ..artifacts import RawRecord
from ..sources import tushare

# Signature of the Tushare call a Capture needs, so tests can fake the Source.
QueryFunc = Callable[..., pd.DataFrame]

# Other Source date facts (contract lifecycle) that Raw records express in the
# same ``YYYY-MM-DD`` form as ``trade_date``. ``maturity_date`` of ``opt_basic``
# is the expiry day of the contract, i.e. the same kind of lifecycle fact as
# ``list_date`` / ``delist_date``.
SOURCE_DATE_FIELDS = ("list_date", "delist_date", "last_ddate", "maturity_date")

# The Source-side failures a Capture reports as its own collection failure.
CAPTURE_FAILURE_TYPES: tuple[type[Exception], ...] = (tushare.TushareSourceError,)


class CollectionError(tushare.TushareSourceError):
    """Raised when a Raw Artifact cannot be collected as its Guide requires.

    It is a ``TushareSourceError`` as well, so a caller that only knows about the
    Source boundary still sees a Source-side failure.
    """


def to_json_scalar(value: Any) -> Any:
    """Convert a numpy scalar to a JSON-compatible scalar; pass others through."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and value != value:  # NaN is not valid JSON.
        return None
    return value


def to_raw_records(frame: pd.DataFrame) -> list[RawRecord]:
    """Turn a Source DataFrame into Raw records (minimal normalization).

    Source fields are kept as-is; only Source date facts are expressed as
    ``YYYY-MM-DD`` (see ``SOURCE_DATE_FIELDS``) and numpy scalars become JSON
    scalars. Missing and already normalized date facts are kept as they are, so
    a Raw record that another Capture re-normalizes stays stable.
    """
    records: list[RawRecord] = []
    for row in frame.to_dict(orient="records"):
        record = {str(key): to_json_scalar(value) for key, value in row.items()}
        for field in (tushare.TRADE_DATE_FIELD, *SOURCE_DATE_FIELDS):
            iso_value = tushare.to_iso_date_or_none(record.get(field))
            if iso_value is not None:
                record[field] = iso_value
        records.append(record)
    return records


def in_date_range(record: RawRecord, field: str, start: str, end: str) -> bool:
    """Report whether ``record[field]`` is an ISO date inside ``[start, end]``."""
    value = record.get(field)
    return isinstance(value, str) and start <= value <= end


def require_target_trade_date(records: Sequence[RawRecord], trade_date: str) -> None:
    """Ensure every collected row belongs to the requested trade date."""
    for record in records:
        if record.get(tushare.TRADE_DATE_FIELD) != trade_date:
            raise CollectionError(
                f"source returned {tushare.TRADE_DATE_FIELD}="
                f"{record.get(tushare.TRADE_DATE_FIELD)!r} "
                f"for requested trade_date={trade_date}."
            )


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
