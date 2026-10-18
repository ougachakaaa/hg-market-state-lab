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
    return tushare.call_provider(
        "index_daily", lambda: api.index_daily(ts_code=ts_code, trade_date=trade_date)
    )


def query_index_daily_range(
    api: tushare.TushareApi, ts_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Read one index over an explicit inclusive range from ``index_daily``."""
    return tushare.call_provider(
        "index_daily",
        lambda: api.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date),
    )


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


def collect_index_observation(
    trade_date: str,
    query: common.QueryFunc,
    index_code: str,
) -> list[artifacts.RawRecord]:
    """Return one index observation, preserving an explicit empty response.

    This is the canonical availability-probe variant of ``index_daily``.  A
    successful empty Source response is returned as an empty Raw row set so the
    product can persist and classify that evidence. Source and normalization
    failures still propagate and therefore cannot be mistaken for absence.
    """
    source_date = tushare.to_tushare_date(trade_date)
    frame = query(ts_code=index_code, trade_date=source_date)
    records = common.to_raw_records(frame)
    if records:
        common.require_target_trade_date(records, trade_date)
        for record in records:
            if record.get("ts_code") != index_code:
                raise common.CollectionError(
                    f"source returned ts_code={record.get('ts_code')!r} "
                    f"for requested index_code={index_code}."
                )
    return records


def capture_observation(
    api: tushare.TushareApi, trade_date: str, index_code: str
) -> list[artifacts.RawRecord]:
    """Run the exact-date ``index_daily`` availability Capture."""
    return collect_index_observation(
        trade_date,
        lambda **kwargs: query_index_daily(api, **kwargs),
        index_code,
    )


def collect_index_range(
    start_trade_date: str,
    end_trade_date: str,
    query: common.QueryFunc,
    index_code: str,
) -> list[artifacts.RawRecord]:
    """Collect and validate one index's facts in an explicit inclusive range."""
    source_start = tushare.to_tushare_date(start_trade_date)
    source_end = tushare.to_tushare_date(end_trade_date)
    records = common.to_raw_records(
        query(ts_code=index_code, start_date=source_start, end_date=source_end)
    )
    for record in records:
        if record.get("ts_code") != index_code:
            raise common.CollectionError(
                f"source returned ts_code={record.get('ts_code')!r} "
                f"for requested index_code={index_code}."
            )
        if not common.in_date_range(
            record, tushare.TRADE_DATE_FIELD, start_trade_date, end_trade_date
        ):
            raise common.CollectionError(
                f"source returned trade_date={record.get('trade_date')!r} "
                f"outside {start_trade_date}..{end_trade_date}."
            )
    records.sort(key=lambda record: str(record["trade_date"]))
    return records


def capture_range(
    api: tushare.TushareApi,
    start_trade_date: str,
    end_trade_date: str,
    index_code: str,
) -> list[artifacts.RawRecord]:
    """Run the explicit-range ``index_daily`` Capture."""
    return collect_index_range(
        start_trade_date,
        end_trade_date,
        lambda **kwargs: query_index_daily_range(api, **kwargs),
        index_code,
    )
