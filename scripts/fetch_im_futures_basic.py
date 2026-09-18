"""Collect the ``im_futures_basic`` Raw Dataset.

Source: Tushare ``fut_basic`` (see ``guides/csi1000-5d-analysis-data.md`` 4.4
and 5.2). The Dataset holds the ordinary monthly IM contracts, not the main /
continuous contracts and not any other CFFEX product.

Usage:
    poetry run python scripts/fetch_im_futures_basic.py 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402

DATASET = "im_futures_basic"
# Dataset membership of the IM universe (Guide 5.2): the Source parameters
# below already limit the response to ordinary monthly IM contracts.
EXCHANGE = "CFFEX"
FUTURES_TYPE_ORDINARY = "1"
PRODUCT = "IM"


def query_fut_basic(
    api: _common.TushareApi, exchange: str, fut_type: str, fut_code: str
) -> pd.DataFrame:
    """Read ordinary CFFEX futures contracts of one product from ``fut_basic``."""
    return api.fut_basic(exchange=exchange, fut_type=fut_type, fut_code=fut_code)


def is_ordinary_monthly_contract(record: _common.RawRecord) -> bool:
    """Report whether a Source fact is an ordinary monthly contract.

    ``fut_basic(fut_type="1")`` should only return ordinary contracts, but the
    main / continuous contract of the product shares the ``fut_code`` value, so
    the contract symbol is checked too: an ordinary monthly symbol carries the
    delivery month (``IM2603``), the continuous symbol does not (``IM``).
    """
    symbol = str(record.get("symbol") or "")
    return symbol.startswith(PRODUCT) and symbol[len(PRODUCT) :].isdigit()


def is_im_contract_member(record: _common.RawRecord) -> bool:
    """Report whether a Source fact belongs to the IM ordinary contract Dataset.

    Dataset membership is decided by the contract identity only: ``CFFEX``,
    ``fut_code=IM`` and an ordinary monthly symbol. Lifecycle facts decide
    whether a member can be placed in a date window, not whether it belongs to
    the Dataset.
    """
    return (
        str(record.get("exchange") or "") == EXCHANGE
        and str(record.get("fut_code") or "") == PRODUCT
        and is_ordinary_monthly_contract(record)
    )


def select_im_contracts(frame: pd.DataFrame) -> list[_common.RawRecord]:
    """Return the ordinary monthly IM contract facts of a ``fut_basic`` response.

    The Source is already asked for ``CFFEX`` / ordinary / ``IM``; the checks
    here only guard the Dataset identity against a Source response that does not
    respect the request, and never filter on liquidity or trading activity.
    """
    records = [
        record for record in _common.to_raw_records(frame) if is_im_contract_member(record)
    ]
    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def require_im_contract_facts(records: Sequence[_common.RawRecord]) -> None:
    """Ensure the collected contract facts are complete and can express a lifecycle.

    Every member contract needs a usable ``list_date`` and ``delist_date``, and
    an inverted lifecycle is invalid. A member with incomplete lifecycle facts is
    still a member, so the Collector fails here instead of dropping it from the
    Dataset.
    """
    if not records:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned no {PRODUCT} contract of exchange={EXCHANGE}."
        )
    codes = [str(record["ts_code"]) for record in records]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        raise _common.CollectionError(
            f"Tushare {DATASET} returned duplicate contract(s): {', '.join(duplicates[:5])}."
        )
    for record in records:
        list_date = _common.to_iso_date_or_none(record.get("list_date"))
        delist_date = _common.to_iso_date_or_none(record.get("delist_date"))
        if list_date is None or delist_date is None:
            raise _common.CollectionError(
                f"{PRODUCT} contract {record.get('ts_code')} has no usable lifecycle facts "
                f"in Tushare {DATASET} (list_date={record.get('list_date')!r}, "
                f"delist_date={record.get('delist_date')!r})."
            )
        if delist_date < list_date:
            raise _common.CollectionError(
                f"{PRODUCT} contract {record.get('ts_code')} has delist_date={delist_date} "
                f"before list_date={list_date}."
            )


def collect_active_im_contracts(query: _common.QueryFunc) -> list[_common.RawRecord]:
    """Return the IM contract facts the Source currently lists.

    Used by the IM daily Collector to identify the contracts of its history
    window; the ``im_futures_basic`` Collector writes the same records out.
    """
    records = select_im_contracts(
        query(exchange=EXCHANGE, fut_type=FUTURES_TYPE_ORDINARY, fut_code=PRODUCT)
    )
    require_im_contract_facts(records)
    return records


def collect_im_futures_basic(trade_date: str, query: _common.QueryFunc) -> list[_common.RawRecord]:
    """Return the ``im_futures_basic`` records for the given target trade date.

    ``fut_basic`` is a contract list without a trade date of its own, so the
    target trade date only validates the script-level date form. Contract
    lifecycle facts are kept as Source facts, delisted contracts included, and a
    member contract with incomplete lifecycle facts fails the collection.
    """
    # Reject a malformed script-level date before any Source request.
    _common.to_tushare_date(trade_date)
    return collect_active_im_contracts(query)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {DATASET} Raw Dataset.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        records = collect_im_futures_basic(
            args.trade_date,
            lambda **kwargs: query_fut_basic(api, **kwargs),
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
