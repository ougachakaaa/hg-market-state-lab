"""Source Capture ``im_futures_daily``: daily facts over the IM window.

Source: Tushare ``fut_daily`` (see ``guides/csi1000-5d-analysis-data.md`` 4.5
and 6.2). The Raw artifact holds the daily facts of the IM ordinary monthly
contracts whose lifecycle overlaps the collection window, so later Analysis
Preparation can rebuild the term structure of about 60 trading days up to the
target date.

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``guides/data-services.md`` 11):

    poetry run python -m daily_market_snapshot.capture.im_futures_daily 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common, im_futures_basic

EXCHANGE = im_futures_basic.EXCHANGE
FUTURES_TYPE_ORDINARY = im_futures_basic.FUTURES_TYPE_ORDINARY
PRODUCT = im_futures_basic.PRODUCT
DATASET = "im_futures_daily"
# Implementation detail, not a data contract: the Guide asks for enough Source
# facts to reach about 60 trading days before the target date, so the Collector
# requests a calendar window that is obviously long enough. The exact window
# selection belongs to Analysis Preparation (Guide 6.2).
COLLECTION_CALENDAR_DAYS = 400


def query_fut_daily(
    api: tushare.TushareApi, ts_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Read one futures contract over a calendar window from Tushare ``fut_daily``."""
    return api.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def window_start_date(target_trade_date: str) -> str:
    """Return the first calendar date of the collection window, in ISO form."""
    start = datetime.strptime(
        target_trade_date, tushare.TRADE_DATE_ISO_FORMAT
    ) - timedelta(days=COLLECTION_CALENDAR_DAYS)
    return start.strftime(tushare.TRADE_DATE_ISO_FORMAT)


def require_contract_lifecycle(record: artifacts.RawRecord) -> tuple[str, str]:
    """Return the ``(list_date, delist_date)`` a window contract needs.

    A member contract without usable lifecycle facts cannot be placed in the
    collection window; that is a Source gap, not a reason to skip the contract.
    """
    list_date = tushare.to_iso_date_or_none(record.get("list_date"))
    delist_date = tushare.to_iso_date_or_none(record.get("delist_date"))
    if list_date is None or delist_date is None:
        raise common.CollectionError(
            f"{PRODUCT} contract {record.get('ts_code')} has no usable lifecycle facts "
            f"in the collected basic records."
        )
    if delist_date < list_date:
        raise common.CollectionError(
            f"{PRODUCT} contract {record.get('ts_code')} has delist_date={delist_date} "
            f"before list_date={list_date}."
        )
    return list_date, delist_date


def effective_range(
    record: artifacts.RawRecord, target_trade_date: str
) -> tuple[str, str] | None:
    """Return the ``(start, end)`` of the contract's effective trading range.

    The range is ``[list_date, min(delist_date, target_trade_date)]``: no fact of
    the contract can exist before it was listed or after it was delisted, and the
    collection itself stops at the target trade date. A contract whose lifecycle
    does not overlap the collection window returns ``None``.
    """
    list_date, delist_date = require_contract_lifecycle(record)
    if delist_date < window_start_date(target_trade_date) or list_date > target_trade_date:
        return None
    return list_date, min(delist_date, target_trade_date)


def in_collection_window(
    record: artifacts.RawRecord, start_date: str, target_trade_date: str
) -> str:
    """Return the contract ``list_date`` if its lifecycle overlaps the window."""
    list_date, delist_date = require_contract_lifecycle(record)
    if list_date <= target_trade_date and delist_date >= start_date:
        return list_date
    return ""


def select_window_contracts(
    basic_records: Sequence[artifacts.RawRecord], start_date: str, target_trade_date: str
) -> list[tuple[artifacts.RawRecord, str]]:
    """Return ``(contract, list_date)`` whose lifecycle overlaps the window."""
    selected: list[tuple[artifacts.RawRecord, str]] = []
    for record in basic_records:
        list_date = in_collection_window(record, start_date, target_trade_date)
        if list_date:
            selected.append((record, list_date))
    return selected


def collect_im_futures_daily(
    trade_date: str,
    basic_frame: pd.DataFrame,
    daily_query: common.QueryFunc,
) -> list[artifacts.RawRecord]:
    """Return the ``im_futures_daily`` records of the target collection window.

    The window is derived from ``im_futures_basic`` contract lifecycles; every
    selected contract is queried over ``[list_date, delist_date]`` capped at the
    target trade date. A contract that has entered its effective trading range
    but returns no daily row is a Source gap and fails, and every returned row
    must belong to the requested contract and to its effective range. Raw rows
    are kept as Source facts and are not trimmed to a trading-day count.
    """
    tushare.to_tushare_date(trade_date)
    start_date = window_start_date(trade_date)
    contracts = select_window_contracts(
        im_futures_basic.select_im_contracts(basic_frame), start_date, trade_date
    )
    if not contracts:
        raise common.CollectionError(
            f"no {PRODUCT} contract lifecycle overlaps {start_date}..{trade_date}; "
            f"{DATASET} needs the contract facts from Tushare fut_basic."
        )

    records: list[artifacts.RawRecord] = []
    for contract, list_date in contracts:
        ts_code = str(contract["ts_code"])
        effective = effective_range(contract, trade_date)
        if effective is None:
            continue
        _, end_date = effective
        frame = daily_query(
            ts_code=ts_code,
            start_date=tushare.to_tushare_date(list_date),
            end_date=tushare.to_tushare_date(end_date),
        )
        contract_records = common.to_raw_records(frame)
        if not contract_records:
            raise common.CollectionError(
                f"Tushare {DATASET} returned no daily row for {PRODUCT} contract {ts_code} "
                f"in its effective range {list_date}..{end_date}."
            )
        for record in contract_records:
            if record.get("ts_code") != ts_code:
                raise common.CollectionError(
                    f"Tushare {DATASET} returned ts_code={record.get('ts_code')!r} "
                    f"for a request of ts_code={ts_code}."
                )
            if not common.in_date_range(
                record, tushare.TRADE_DATE_FIELD, list_date, end_date
            ):
                raise common.CollectionError(
                    f"Tushare {DATASET} returned {tushare.TRADE_DATE_FIELD}="
                    f"{record.get(tushare.TRADE_DATE_FIELD)!r} for {ts_code} "
                    f"outside {list_date}..{end_date}."
                )
        records.extend(contract_records)

    records.sort(
        key=lambda record: (str(record["ts_code"]), record[tushare.TRADE_DATE_FIELD])
    )
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw artifact.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        basic_frame = im_futures_basic.query_fut_basic(
            api,
            exchange=EXCHANGE,
            fut_type=FUTURES_TYPE_ORDINARY,
            fut_code=PRODUCT,
        )
        records = collect_im_futures_daily(
            args.trade_date,
            basic_frame,
            lambda **kwargs: query_fut_daily(api, **kwargs),
        )
    except common.CAPTURE_FAILURE_TYPES as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    path = artifacts.write_raw_artifact(
        records, artifacts.csi1000_raw_dir(args.trade_date), DATASET
    )
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
