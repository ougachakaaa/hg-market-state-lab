"""Collect the ``index_daily`` Raw Dataset for CSI1000, up to a target trade date.

Source: Tushare ``index_daily`` (see ``guides/csi1000-5d-analysis-data.md`` 4.1
and 6.1).

Usage:
    poetry run python scripts/fetch_csi1000_index_history.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402

DATASET = "index_daily_history"
# Dataset identity of the CSI1000 history window (Guide 4.1).
INDEX_CODE = "000852.SH"
# Implementation detail, not a data contract: the Guide asks for enough Source
# facts to reach the latest 120 trading days, so the Collector requests a
# calendar window that is obviously long enough. The exact window selection
# belongs to later assembly (Guide 6.1).
LOOKBACK_CALENDAR_DAYS = 240
# Completeness requirement of the same Guide 6.1 window: the Raw artifact must
# let downstream assembly reach the latest 120 *actual* trading days, so at
# least this many distinct trade dates have to be present. The Raw artifact is
# not trimmed to exactly this count.
MIN_HISTORY_TRADE_DATES = 120


def query_index_daily_history(
    api: _common.TushareApi, ts_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Read one index over a calendar window from Tushare ``index_daily``."""
    return api.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def lookback_window(target_trade_date: str) -> tuple[str, str]:
    """Return the requested history window as Source-form ``(start, end)`` dates."""
    end_date = _common.to_tushare_date(target_trade_date)
    start = datetime.strptime(target_trade_date, _common.TRADE_DATE_ISO_FORMAT) - timedelta(
        days=LOOKBACK_CALENDAR_DAYS
    )
    return start.strftime(_common.TRADE_DATE_TUSHARE_FORMAT), end_date


def require_history_window(
    records: Sequence[_common.RawRecord], start_date: str, target_trade_date: str
) -> None:
    """Ensure the history is complete enough for the Guide 6.1 window.

    The history must cover at least ``MIN_HISTORY_TRADE_DATES`` distinct trade
    dates ending at ``target_trade_date``, hold one Source row per trade date,
    and describe only ``INDEX_CODE``. The Raw artifact is not trimmed to that
    count: the exact ``latest 120 trading rows`` selection stays assembly.
    """
    if not records:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no data for ts_code={INDEX_CODE} "
            f"on or before trade_date={target_trade_date}."
        )

    seen: set[tuple[str, str]] = set()
    for record in records:
        if record.get("ts_code") != INDEX_CODE:
            raise _common.CollectionError(
                f"Tushare {DATASET} returned ts_code={record.get('ts_code')!r} "
                f"for a request of ts_code={INDEX_CODE}."
            )
        in_window = _common.in_date_range(
            record, _common.TRADE_DATE_FIELD, start_date, target_trade_date
        )
        if not in_window:
            raise _common.CollectionError(
                f"Tushare {DATASET} returned {_common.TRADE_DATE_FIELD}="
                f"{record.get(_common.TRADE_DATE_FIELD)!r} outside the requested window "
                f"{start_date}..{target_trade_date}."
            )
        key = (str(record["ts_code"]), str(record[_common.TRADE_DATE_FIELD]))
        if key in seen:
            raise _common.CollectionError(
                f"Tushare {DATASET} returned duplicate rows for ts_code={key[0]} "
                f"trade_date={key[1]}."
            )
        seen.add(key)

    trade_dates = {str(record[_common.TRADE_DATE_FIELD]) for record in records}
    if target_trade_date not in trade_dates:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no record for ts_code={INDEX_CODE} "
            f"on trade_date={target_trade_date}."
        )
    if len(trade_dates) < MIN_HISTORY_TRADE_DATES:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned only {len(trade_dates)} distinct "
            f"{_common.TRADE_DATE_FIELD} values for ts_code={INDEX_CODE}, fewer than the "
            f"{MIN_HISTORY_TRADE_DATES} the analysis window needs."
        )


def collect_index_daily_history(
    trade_date: str, query: _common.QueryFunc
) -> list[_common.RawRecord]:
    """Return the ``index_daily`` history records of ``000852.SH``.

    The Raw artifact covers a range of trade dates; the window bounds and the
    completeness requirement (at least ``MIN_HISTORY_TRADE_DATES`` distinct
    trade dates ending at the target date) are checked here. Selecting the
    latest 120 trading rows is assembly.
    """
    start_date, end_date = lookback_window(trade_date)
    frame = query(ts_code=INDEX_CODE, start_date=start_date, end_date=end_date)
    records = _common.to_raw_records(frame)
    source_start = _common.to_iso_date(start_date)
    records.sort(key=lambda record: record[_common.TRADE_DATE_FIELD])
    require_history_window(records, source_start, trade_date)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw Dataset.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        records = collect_index_daily_history(
            args.trade_date,
            lambda **kwargs: query_index_daily_history(api, **kwargs),
        )
    except _common.CollectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    dataset_dir = _common.RAW_DIR / _common.CSI1000_RAW_SUBDIR / args.trade_date
    path = _common.write_raw_dataset(records, dataset_dir, DATASET)
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
