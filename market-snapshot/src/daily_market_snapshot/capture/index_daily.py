"""Shared Tushare ``index_daily`` Source Capture.

Source: Tushare ``index_daily`` (see ``capture/ARCHITECTURE.md`` section 3;
Product contexts pass their own explicit index universe; this shared Capture
owns only the Source endpoint, normalization and target-date validation.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common

RAW_ARTIFACT = "index_daily"


class NoIndexDataError(common.CollectionError):
    """The requested date has no index observation from the Source."""


def query_index_daily(api: tushare.TushareApi, ts_code: str, trade_date: str) -> pd.DataFrame:
    """Read one index for one trade date from Tushare ``index_daily``."""
    return api.index_daily(ts_code=ts_code, trade_date=trade_date)


def collect_index_daily(
    trade_date: str,
    query: common.QueryFunc,
    index_codes: Sequence[str],
) -> list[artifacts.RawRecord]:
    """Return the ``index_daily`` records for every index in the universe."""
    tushare_date = tushare.to_tushare_date(trade_date)
    records: list[artifacts.RawRecord] = []
    for ts_code in index_codes:
        frame = query(ts_code=ts_code, trade_date=tushare_date)
        if frame.empty:
            continue
        records.extend(common.to_raw_records(frame))

    if not records:
        raise NoIndexDataError(
            f"Tushare {RAW_ARTIFACT} returned no data for trade_date={trade_date}."
        )

    common.require_target_trade_date(records, trade_date)
    return records
