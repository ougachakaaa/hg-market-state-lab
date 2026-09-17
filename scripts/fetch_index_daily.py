"""Collect the ``index_daily`` Raw Dataset for one trade date.

Source: Tushare ``index_daily`` (see ``guides/daily-market-snapshot.md`` 4.1).

Usage:
    poetry run python scripts/fetch_index_daily.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402

DATASET = "index_daily"
# The fixed Phase 1 index observation universe (Guide 4.1).
INDEX_CODES = (
    "000016.SH",
    "000300.SH",
    "000905.SH",
    "000852.SH",
    "399006.SZ",
    "000688.SH",
)


def query_index_daily(api: _common.TushareApi, ts_code: str, trade_date: str) -> pd.DataFrame:
    """Read one index for one trade date from Tushare ``index_daily``."""
    return api.index_daily(ts_code=ts_code, trade_date=trade_date)


def collect_index_daily(
    trade_date: str,
    query: _common.QueryFunc,
    index_codes: Sequence[str] = INDEX_CODES,
) -> list[_common.RawRecord]:
    """Return the ``index_daily`` records for every index in the universe."""
    tushare_date = _common.to_tushare_date(trade_date)
    records: list[_common.RawRecord] = []
    for ts_code in index_codes:
        frame = query(ts_code=ts_code, trade_date=tushare_date)
        if frame.empty:
            continue
        records.extend(_common.to_raw_records(frame))

    if not records:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no data for trade_date={trade_date}."
        )

    _common.require_target_trade_date(records, trade_date)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw Dataset.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        records = collect_index_daily(
            args.trade_date,
            lambda **kwargs: query_index_daily(api, **kwargs),
        )
    except _common.CollectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    path = _common.write_raw_dataset(records, _common.RAW_DIR / args.trade_date, DATASET)
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
