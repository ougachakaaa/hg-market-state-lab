"""CFFEX equity-index futures ordinary monthly contract Source facts.

Source: Tushare ``fut_basic``; shared Source facts are defined by
``capture/im-futures-contract.md``.
The family parameter supports IF/IH/IC/IM while the default preserves IM
callers. Main and continuous symbols are outside Capture scope.

"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common

RAW_ARTIFACT = "im_futures_basic"
# The default preserves the existing IM Capture callers.
EXCHANGE = "CFFEX"
FUTURES_TYPE_ORDINARY = "1"
PRODUCT = "IM"
FAMILIES = frozenset({"IF", "IH", "IC", "IM"})


def _family(family: str) -> str:
    if family not in FAMILIES:
        raise common.CollectionError(f"unsupported CFFEX futures family {family!r}.")
    return family


def query_fut_basic(
    api: tushare.TushareApi, exchange: str, fut_type: str, fut_code: str
) -> pd.DataFrame:
    """Read ordinary CFFEX futures contracts of one product from ``fut_basic``."""
    return api.fut_basic(exchange=exchange, fut_type=fut_type, fut_code=fut_code)


def is_ordinary_monthly_contract(record: artifacts.RawRecord, family: str = PRODUCT) -> bool:
    """Report whether a Source fact is an ordinary monthly contract.

    ``fut_basic(fut_type="1")`` should only return ordinary contracts, but the
    main / continuous contract of the product shares the ``fut_code`` value, so
    the contract symbol is checked too: an ordinary monthly symbol carries the
    delivery month (``IM2603``), the continuous symbol does not (``IM``).
    """
    symbol = str(record.get("symbol") or "")
    # Keep malformed numeric candidates for explicit product-level validation;
    # only main/continuous symbols without a delivery suffix are excluded.
    return symbol.startswith(family) and symbol[len(family) :].isdigit()


def is_im_contract_member(record: artifacts.RawRecord, family: str = PRODUCT) -> bool:
    """Report whether a Source fact belongs to the IM ordinary contract scope.

    Capture scope is decided by the contract identity only: ``CFFEX``,
    ``fut_code=IM`` and an ordinary monthly symbol. Lifecycle facts decide
    whether a member can be placed in a date window, not whether it is in scope.
    """
    return (
        str(record.get("exchange") or "") == EXCHANGE
        and str(record.get("fut_code") or "") == family
        and is_ordinary_monthly_contract(record, family)
    )


def select_im_contracts(frame: pd.DataFrame, family: str = PRODUCT) -> list[artifacts.RawRecord]:
    """Return the ordinary monthly IM contract facts of a ``fut_basic`` response.

    The Source is already asked for ``CFFEX`` / ordinary / ``IM``; the checks
    here only guard the Capture scope against a Source response that does not
    respect the request, and never filter on liquidity or trading activity.
    """
    records = [
        record for record in common.to_raw_records(frame) if is_im_contract_member(record, family)
    ]
    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def require_im_contract_facts(
    records: Sequence[artifacts.RawRecord], family: str = PRODUCT
) -> None:
    """Ensure the collected contract facts are complete and can express a lifecycle.

    Every contract in scope needs a usable ``list_date`` and ``delist_date``, and
    an inverted lifecycle is invalid. A contract with incomplete lifecycle facts
    is still in scope, so the Capture fails here instead of dropping it.
    """
    if not records:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no {family} contract of exchange={EXCHANGE}."
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
                f"{family} contract {record.get('ts_code')} has no usable lifecycle facts "
                f"in Tushare {RAW_ARTIFACT} (list_date={record.get('list_date')!r}, "
                f"delist_date={record.get('delist_date')!r})."
            )
        if delist_date < list_date:
            raise common.CollectionError(
                f"{family} contract {record.get('ts_code')} has delist_date={delist_date} "
                f"before list_date={list_date}."
            )


def collect_active_im_contracts(
    query: common.QueryFunc, family: str = PRODUCT
) -> list[artifacts.RawRecord]:
    """Return the IM contract facts the Source currently lists.

    Used by the IM daily Capture to identify the contracts of its history
    window; the ``im_futures_basic`` Capture collects the same records.
    """
    family = _family(family)
    records = select_im_contracts(
        query(exchange=EXCHANGE, fut_type=FUTURES_TYPE_ORDINARY, fut_code=family), family
    )
    require_im_contract_facts(records, family)
    return records


def collect_im_futures_basic(
    trade_date: str, query: common.QueryFunc, family: str = PRODUCT
) -> list[artifacts.RawRecord]:
    """Return the ``im_futures_basic`` records for the given target trade date.

    ``fut_basic`` is a contract list without a trade date of its own, so the
    target trade date only validates the project-level date form. Contract
    lifecycle facts are kept as Source facts, delisted contracts included, and a
    contract with incomplete lifecycle facts fails the collection.
    """
    # Reject a malformed project-level date before any Source request.
    tushare.to_tushare_date(trade_date)
    return collect_active_im_contracts(query, family)


def capture(
    api: tushare.TushareApi, trade_date: str, family: str = PRODUCT
) -> list[artifacts.RawRecord]:
    """Run this Source Capture for one target trade date against a Source api.

    The endpoint and its query parameters (``exchange`` / ``fut_type`` /
    ``fut_code``) stay in this module; an active Product asks for the Capture.
    """
    return collect_im_futures_basic(
        trade_date, lambda **kwargs: query_fut_basic(api, **kwargs), family
    )
