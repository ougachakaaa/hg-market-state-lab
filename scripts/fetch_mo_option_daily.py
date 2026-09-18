"""Collect the ``mo_option_daily`` Raw Dataset for one trade date.

Source: Tushare ``opt_daily`` (see ``guides/csi1000-5d-analysis-data.md`` 4.3
and 5.1). Only the daily facts of the active MO option universe of the target
trade date belong to this Dataset.

Usage:
    poetry run python scripts/fetch_mo_option_daily.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
from fetch_mo_option_basic import (  # noqa: E402
    EXCHANGE,
    PRODUCT,
    query_opt_basic,
    select_active_mo_universe,
)

DATASET = "mo_option_daily"


def query_opt_daily(api: _common.TushareApi, trade_date: str, exchange: str) -> pd.DataFrame:
    """Read one trade date of CFFEX option quotes from Tushare ``opt_daily``."""
    return api.opt_daily(trade_date=trade_date, exchange=exchange)


def collect_mo_option_daily(
    trade_date: str,
    basic_frame: pd.DataFrame,
    query: _common.QueryFunc,
) -> list[_common.RawRecord]:
    """Return the ``mo_option_daily`` records of the active MO universe.

    ``basic_frame`` is the ``opt_basic`` Source response; the same active
    universe rule as ``mo_option_basic`` is applied to it, so both Raw artifacts
    describe the same contract identity.
    """
    tushare_date = _common.to_tushare_date(trade_date)
    universe = select_active_mo_universe(basic_frame, trade_date)
    if not universe:
        raise _common.CollectionError(
            f"no active {PRODUCT} contract on trade_date={trade_date}; "
            f"{DATASET} needs the active universe from Tushare opt_basic."
        )
    universe_codes = {str(record["ts_code"]) for record in universe}

    frame = query(trade_date=tushare_date, exchange=EXCHANGE)
    records = _common.to_raw_records(frame)
    if not records:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no data for trade_date={trade_date}."
        )
    _common.require_target_trade_date(records, trade_date)

    outside_universe = sorted(
        {
            str(record["ts_code"])
            for record in records
            if record.get("ts_code") not in universe_codes
        }
    )
    if outside_universe:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned {len(outside_universe)} "
            f"{PRODUCT} contract(s) that are not in the active universe on "
            f"trade_date={trade_date}: {', '.join(outside_universe[:5])}."
        )

    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw Dataset.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        basic_frame = query_opt_basic(api, EXCHANGE)
        records = collect_mo_option_daily(
            args.trade_date,
            basic_frame,
            lambda **kwargs: query_opt_daily(api, **kwargs),
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
