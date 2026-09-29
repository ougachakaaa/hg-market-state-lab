"""CFFEX equity-index futures daily Capture for target-date and range Products."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common, im_futures_basic

PRODUCT = im_futures_basic.PRODUCT
RAW_ARTIFACT = "im_futures_daily"


def query_fut_daily(
    api: tushare.TushareApi, ts_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Read one futures contract over a calendar window from Tushare ``fut_daily``."""
    return api.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def query_target_date_fut_daily(
    api: tushare.TushareApi, ts_code: str, trade_date: str
) -> pd.DataFrame:
    """Read only one contract's target-date fact from the same Source endpoint."""
    return api.fut_daily(ts_code=ts_code, trade_date=trade_date)


def require_contract_lifecycle(
    record: artifacts.RawRecord, family: str = PRODUCT
) -> tuple[str, str]:
    """Return the ``(list_date, delist_date)`` an IM contract needs.

    A member contract without usable lifecycle facts cannot be placed in the
    requested date range; that is a Source gap, not a reason to skip the contract.
    """
    list_date = tushare.to_iso_date_or_none(record.get("list_date"))
    delist_date = tushare.to_iso_date_or_none(record.get("delist_date"))
    if list_date is None or delist_date is None:
        raise common.CollectionError(
            f"{family} contract {record.get('ts_code')} has no usable lifecycle facts "
            f"in the collected basic records."
        )
    if delist_date < list_date:
        raise common.CollectionError(
            f"{family} contract {record.get('ts_code')} has delist_date={delist_date} "
            f"before list_date={list_date}."
        )
    return list_date, delist_date


def collect_target_date_im_futures_daily(
    trade_date: str,
    basic_facts: Sequence[artifacts.RawRecord],
    daily_query: common.QueryFunc,
    family: str = PRODUCT,
) -> list[artifacts.RawRecord]:
    """Collect target-date facts for every active ordinary monthly IM contract.

    A missing Source row is preserved as an absence in Raw. Preparation decides
    whether that contract is needed by an MO expiry and therefore required for
    a complete read model.
    """
    source_date = tushare.to_tushare_date(trade_date)
    im_futures_basic.require_im_contract_facts(basic_facts, family)
    records: list[artifacts.RawRecord] = []
    for contract in basic_facts:
        if not im_futures_basic.is_im_contract_member(contract, family):
            raise common.CollectionError(f"{family} basic facts include a contract outside scope")
        list_date, delist_date = require_contract_lifecycle(contract, family)
        if not list_date <= trade_date <= delist_date:
            continue
        ts_code = str(contract["ts_code"])
        contract_records = common.to_raw_records(
            daily_query(ts_code=ts_code, trade_date=source_date)
        )
        for record in contract_records:
            if record.get("ts_code") != ts_code:
                raise common.CollectionError(
                    f"Tushare {RAW_ARTIFACT} returned ts_code={record.get('ts_code')!r} "
                    f"for a request of ts_code={ts_code}."
                )
        common.require_target_trade_date(contract_records, trade_date)
        records.extend(contract_records)
    records.sort(key=lambda record: (str(record["ts_code"]), record["trade_date"]))
    return records


def collect_im_futures_daily_range(
    start_trade_date: str,
    end_trade_date: str,
    basic_facts: Sequence[artifacts.RawRecord],
    daily_query: common.QueryFunc,
    family: str = PRODUCT,
) -> list[artifacts.RawRecord]:
    """Collect daily facts for every IM lifecycle intersecting an explicit range."""
    tushare.to_tushare_date(start_trade_date)
    tushare.to_tushare_date(end_trade_date)
    im_futures_basic.require_im_contract_facts(basic_facts, family)
    records: list[artifacts.RawRecord] = []
    selected = 0
    for contract in basic_facts:
        if not im_futures_basic.is_im_contract_member(contract, family):
            raise common.CollectionError(f"{family} basic facts include a contract outside scope")
        list_date, delist_date = require_contract_lifecycle(contract, family)
        if list_date > end_trade_date or delist_date < start_trade_date:
            continue
        selected += 1
        ts_code = str(contract["ts_code"])
        effective_start = max(start_trade_date, list_date)
        effective_end = min(end_trade_date, delist_date)
        contract_records = common.to_raw_records(
            daily_query(
                ts_code=ts_code,
                start_date=tushare.to_tushare_date(effective_start),
                end_date=tushare.to_tushare_date(effective_end),
            )
        )
        for record in contract_records:
            if record.get("ts_code") != ts_code:
                raise common.CollectionError(
                    f"Tushare {RAW_ARTIFACT} returned ts_code={record.get('ts_code')!r} "
                    f"for a request of ts_code={ts_code}."
                )
            if not common.in_date_range(
                record, tushare.TRADE_DATE_FIELD, effective_start, effective_end
            ):
                raise common.CollectionError(
                    f"Tushare {RAW_ARTIFACT} returned trade_date="
                    f"{record.get('trade_date')!r} for {ts_code} outside "
                    f"{effective_start}..{effective_end}."
                )
        records.extend(contract_records)
    if not selected:
        raise common.CollectionError(
            f"no {family} contract lifecycle intersects {start_trade_date}..{end_trade_date}."
        )
    records.sort(key=lambda record: (str(record["ts_code"]), str(record["trade_date"])))
    return records


def capture_range(
    api: tushare.TushareApi,
    start_trade_date: str,
    end_trade_date: str,
    basic_facts: Sequence[artifacts.RawRecord],
    family: str = PRODUCT,
) -> list[artifacts.RawRecord]:
    """Run the explicit-range ``fut_daily`` Capture."""
    return collect_im_futures_daily_range(
        start_trade_date,
        end_trade_date,
        basic_facts,
        lambda **kwargs: query_fut_daily(api, **kwargs),
        family,
    )


def capture_target_date(
    api: tushare.TushareApi,
    trade_date: str,
    basic_facts: Sequence[artifacts.RawRecord],
    family: str = PRODUCT,
) -> list[artifacts.RawRecord]:
    """Capture one day's IM facts for active Products."""
    return collect_target_date_im_futures_daily(
        trade_date,
        basic_facts,
        lambda **kwargs: query_target_date_fut_daily(api, **kwargs),
        family,
    )
