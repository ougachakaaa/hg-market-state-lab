"""Source Capture ``index_daily``: one trade date of the index observation universe.

Source: Tushare ``index_daily`` (see ``market-snapshot/guides/source-captures.md`` section 3;
the product scope is in ``market-snapshot/guides/daily-market-snapshot/index.md`` 4.1).

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``market-snapshot/guides/data-services.md`` section 4):

    poetry run python -m daily_market_snapshot.capture.index_daily 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common

RAW_ARTIFACT = "index_daily"
# The fixed Phase 1 index observation universe (Guide 4.1).
INDEX_CODES = (
    "000016.SH",
    "000300.SH",
    "000905.SH",
    "000852.SH",
    "399006.SZ",
    "000688.SH",
)


class NoIndexDataError(common.CollectionError):
    """The requested date has no index observation from the Source."""


def query_index_daily(api: tushare.TushareApi, ts_code: str, trade_date: str) -> pd.DataFrame:
    """Read one index for one trade date from Tushare ``index_daily``."""
    return api.index_daily(ts_code=ts_code, trade_date=trade_date)


def collect_index_daily(
    trade_date: str,
    query: common.QueryFunc,
    index_codes: Sequence[str] = INDEX_CODES,
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {RAW_ARTIFACT} Raw artifact.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        records = collect_index_daily(
            args.trade_date,
            lambda **kwargs: query_index_daily(api, **kwargs),
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
