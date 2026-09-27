"""Source Capture ``stock_daily``: one trade date of the A-share daily quotes.

Source: Tushare ``daily`` (see ``capture/ARCHITECTURE.md`` section 4;
the product scope is in ``products/daily_market_snapshot/data.md`` 4.2).

Product-local development / debugging entrypoint for its Raw path:

    poetry run python -m market_snapshot.products.daily_market_snapshot.stock_daily 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from ... import artifacts
from ...capture import common
from ...sources import tushare
from .raw import raw_dir

RAW_ARTIFACT = "stock_daily"


def query_stock_daily(api: tushare.TushareApi, trade_date: str) -> pd.DataFrame:
    """Read all A-share daily quotes of one trade date from Tushare ``daily``."""
    return api.daily(trade_date=trade_date)


def collect_stock_daily(trade_date: str, query: common.QueryFunc) -> list[artifacts.RawRecord]:
    """Return the ``stock_daily`` records for the given trade date."""
    tushare_date = tushare.to_tushare_date(trade_date)
    records = common.to_raw_records(query(trade_date=tushare_date))

    if not records:
        raise common.CollectionError(
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
        records = collect_stock_daily(
            args.trade_date,
            lambda **kwargs: query_stock_daily(api, **kwargs),
        )
    except common.CAPTURE_FAILURE_TYPES as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    path = artifacts.write_raw_artifact(
        records, raw_dir(args.trade_date), RAW_ARTIFACT
    )
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
