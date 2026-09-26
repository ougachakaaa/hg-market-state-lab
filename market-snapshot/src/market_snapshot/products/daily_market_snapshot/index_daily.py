"""Daily Market Snapshot adapter for the shared ``index_daily`` Capture."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from ... import artifacts
from ...capture import common
from ...capture import index_daily as shared
from ...sources import tushare

RAW_ARTIFACT = shared.RAW_ARTIFACT
NoIndexDataError = shared.NoIndexDataError

INDEX_CODES = (
    "000016.SH",
    "000300.SH",
    "000905.SH",
    "000852.SH",
    "399006.SZ",
    "000688.SH",
)


def query_index_daily(
    api: tushare.TushareApi, ts_code: str, trade_date: str
) -> pd.DataFrame:
    """Delegate the Source call to the shared Capture."""
    return shared.query_index_daily(api, ts_code, trade_date)


def collect_index_daily(
    trade_date: str, query: common.QueryFunc
) -> list[artifacts.RawRecord]:
    """Collect the scenario's fixed six-index observation universe."""
    return shared.collect_index_daily(trade_date, query, INDEX_CODES)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {RAW_ARTIFACT} Raw artifact.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)
    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        records = collect_index_daily(
            args.trade_date, lambda **kwargs: query_index_daily(api, **kwargs)
        )
    except common.CAPTURE_FAILURE_TYPES as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    path = artifacts.write_raw_artifact(
        records, artifacts.daily_raw_dir(args.trade_date), RAW_ARTIFACT
    )
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
