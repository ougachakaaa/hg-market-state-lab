"""Source Capture ``im_futures_basic``: the IM ordinary monthly contract facts.

Source: Tushare ``fut_basic`` (see ``market-snapshot/guides/source-captures.md`` section 7;
the product universe is in ``market-snapshot/guides/csi1000-5d-analysis/data.md`` section 4.2).
The Capture scope holds the ordinary monthly IM contracts, not the
main / continuous contracts and not any other CFFEX product.

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``market-snapshot/guides/data-services.md`` section 4):

    poetry run python -m daily_market_snapshot.capture.im_futures_basic 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common

RAW_ARTIFACT = "im_futures_basic"
# Capture scope of the IM universe (Guide 5.2): the Source parameters below
# already limit the response to ordinary monthly IM contracts.
EXCHANGE = "CFFEX"
FUTURES_TYPE_ORDINARY = "1"
PRODUCT = "IM"


def query_fut_basic(
    api: tushare.TushareApi, exchange: str, fut_type: str, fut_code: str
) -> pd.DataFrame:
    """Read ordinary CFFEX futures contracts of one product from ``fut_basic``."""
    return api.fut_basic(exchange=exchange, fut_type=fut_type, fut_code=fut_code)


def is_ordinary_monthly_contract(record: artifacts.RawRecord) -> bool:
    """Report whether a Source fact is an ordinary monthly contract.

    ``fut_basic(fut_type="1")`` should only return ordinary contracts, but the
    main / continuous contract of the product shares the ``fut_code`` value, so
    the contract symbol is checked too: an ordinary monthly symbol carries the
    delivery month (``IM2603``), the continuous symbol does not (``IM``).
    """
    symbol = str(record.get("symbol") or "")
    return symbol.startswith(PRODUCT) and symbol[len(PRODUCT) :].isdigit()


def is_im_contract_member(record: artifacts.RawRecord) -> bool:
    """Report whether a Source fact belongs to the IM ordinary contract scope.

    Capture scope is decided by the contract identity only: ``CFFEX``,
    ``fut_code=IM`` and an ordinary monthly symbol. Lifecycle facts decide
    whether a member can be placed in a date window, not whether it is in scope.
    """
    return (
        str(record.get("exchange") or "") == EXCHANGE
        and str(record.get("fut_code") or "") == PRODUCT
        and is_ordinary_monthly_contract(record)
    )


def select_im_contracts(frame: pd.DataFrame) -> list[artifacts.RawRecord]:
    """Return the ordinary monthly IM contract facts of a ``fut_basic`` response.

    The Source is already asked for ``CFFEX`` / ordinary / ``IM``; the checks
    here only guard the Capture scope against a Source response that does not
    respect the request, and never filter on liquidity or trading activity.
    """
    records = [
        record for record in common.to_raw_records(frame) if is_im_contract_member(record)
    ]
    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def require_im_contract_facts(records: Sequence[artifacts.RawRecord]) -> None:
    """Ensure the collected contract facts are complete and can express a lifecycle.

    Every contract in scope needs a usable ``list_date`` and ``delist_date``, and
    an inverted lifecycle is invalid. A contract with incomplete lifecycle facts
    is still in scope, so the Capture fails here instead of dropping it.
    """
    if not records:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no {PRODUCT} contract of exchange={EXCHANGE}."
        )
    codes = [str(record["ts_code"]) for record in records]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned duplicate contract(s): {', '.join(duplicates[:5])}."
        )
    for record in records:
        list_date = tushare.to_iso_date_or_none(record.get("list_date"))
        delist_date = tushare.to_iso_date_or_none(record.get("delist_date"))
        if list_date is None or delist_date is None:
            raise common.CollectionError(
                f"{PRODUCT} contract {record.get('ts_code')} has no usable lifecycle facts "
                f"in Tushare {RAW_ARTIFACT} (list_date={record.get('list_date')!r}, "
                f"delist_date={record.get('delist_date')!r})."
            )
        if delist_date < list_date:
            raise common.CollectionError(
                f"{PRODUCT} contract {record.get('ts_code')} has delist_date={delist_date} "
                f"before list_date={list_date}."
            )


def collect_active_im_contracts(query: common.QueryFunc) -> list[artifacts.RawRecord]:
    """Return the IM contract facts the Source currently lists.

    Used by the IM daily Capture to identify the contracts of its history
    window; the ``im_futures_basic`` Capture collects the same records.
    """
    records = select_im_contracts(
        query(exchange=EXCHANGE, fut_type=FUTURES_TYPE_ORDINARY, fut_code=PRODUCT)
    )
    require_im_contract_facts(records)
    return records


def collect_im_futures_basic(
    trade_date: str, query: common.QueryFunc
) -> list[artifacts.RawRecord]:
    """Return the ``im_futures_basic`` records for the given target trade date.

    ``fut_basic`` is a contract list without a trade date of its own, so the
    target trade date only validates the project-level date form. Contract
    lifecycle facts are kept as Source facts, delisted contracts included, and a
    contract with incomplete lifecycle facts fails the collection.
    """
    # Reject a malformed project-level date before any Source request.
    tushare.to_tushare_date(trade_date)
    return collect_active_im_contracts(query)


def capture(api: tushare.TushareApi, trade_date: str) -> list[artifacts.RawRecord]:
    """Run this Source Capture for one target trade date against a Source api.

    The endpoint and its query parameters (``exchange`` / ``fut_type`` /
    ``fut_code``) stay in this module; a caller (the Data Service or the
    development entrypoint) only asks for the Capture (``ARCHITECTURE.md`` 2).
    """
    return collect_im_futures_basic(
        trade_date, lambda **kwargs: query_fut_basic(api, **kwargs)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {RAW_ARTIFACT} Raw artifact.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        records = capture(api, args.trade_date)
    except common.CAPTURE_FAILURE_TYPES as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    path = artifacts.write_raw_artifact(
        records, artifacts.csi1000_raw_dir(args.trade_date), RAW_ARTIFACT
    )
    print(f"wrote {len(records)} records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
