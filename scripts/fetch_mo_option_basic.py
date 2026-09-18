"""Collect the ``mo_option_basic`` Raw Dataset for one trade date.

Source: Tushare ``opt_basic`` (see ``guides/csi1000-5d-analysis-data.md`` 4.2
and 5.1).

Usage:
    poetry run python scripts/fetch_mo_option_basic.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402

DATASET = "mo_option_basic"
# Dataset membership of the MO chain (Guide 5.1). These limits select the
# Dataset, not an analysis subset.
EXCHANGE = "CFFEX"
PRODUCT = "MO"
MO_OPTIONS_CODE = "OPMO"


def query_opt_basic(api: _common.TushareApi, exchange: str) -> pd.DataFrame:
    """Read the CFFEX option contract facts from Tushare ``opt_basic``.

    ``opt_basic`` has no product parameter, so the product limit below is
    applied to the returned Source facts.
    """
    return api.opt_basic(exchange=exchange)


def is_mo_option(record: _common.RawRecord) -> bool:
    """Report whether a CFFEX option contract fact belongs to the MO product.

    ``opt_basic`` expresses ``opt_code`` as the underlying futures contract of
    the option (``OPMO2609.CFE`` for MO), which is the Source fact that
    identifies the product; the contract name is not used, so the check stays
    independent of naming conventions.
    """
    return str(record.get("opt_code") or "").startswith(MO_OPTIONS_CODE)


def lifecycle_covers(record: _common.RawRecord, trade_date: str) -> bool:
    """Apply the Source-fact lifecycle rule ``list_date <= date <= delist_date``."""
    list_date = _common.to_iso_date_or_none(record.get("list_date"))
    delist_date = _common.to_iso_date_or_none(record.get("delist_date"))
    if list_date is not None and trade_date < list_date:
        return False
    return not (delist_date is not None and trade_date > delist_date)


def select_active_mo_universe(
    frame: pd.DataFrame, trade_date: str
) -> list[_common.RawRecord]:
    """Return the active MO option contract facts of one trade date."""
    return [
        record
        for record in _common.to_raw_records(frame)
        if str(record.get("exchange") or "") == EXCHANGE
        and is_mo_option(record)
        and lifecycle_covers(record, trade_date)
    ]


def collect_mo_option_basic(trade_date: str, query: _common.QueryFunc) -> list[_common.RawRecord]:
    """Return the ``mo_option_basic`` records for the given trade date."""
    # Reject a malformed script-level date before any Source request.
    _common.to_tushare_date(trade_date)
    records = select_active_mo_universe(query(exchange=EXCHANGE), trade_date)

    if not records:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no active {PRODUCT} contract on "
            f"trade_date={trade_date}."
        )

    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw Dataset.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        records = collect_mo_option_basic(
            args.trade_date,
            lambda **kwargs: query_opt_basic(api, **kwargs),
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
