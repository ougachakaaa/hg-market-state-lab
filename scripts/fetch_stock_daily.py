"""Collect the ``stock_daily`` Raw Dataset for one trade date.

Source: Tushare ``daily`` (see ``guides/daily-market-snapshot.md`` 4.2).

Usage:
    poetry run python scripts/fetch_stock_daily.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402

DATASET = "stock_daily"


def query_stock_daily(api: _common.TushareApi, trade_date: str) -> pd.DataFrame:
    """Read all A-share daily quotes of one trade date from Tushare ``daily``."""
    return api.daily(trade_date=trade_date)


def collect_stock_daily(trade_date: str, query: _common.QueryFunc) -> list[_common.RawRecord]:
    """Return the ``stock_daily`` records for the given trade date."""
    tushare_date = _common.to_tushare_date(trade_date)
    records = _common.to_raw_records(query(trade_date=tushare_date))

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
        records = collect_stock_daily(
            args.trade_date,
            lambda **kwargs: query_stock_daily(api, **kwargs),
        )
    except _common.CollectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    path = _common.write_raw_dataset(records, _common.RAW_DIR / args.trade_date, DATASET)
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
