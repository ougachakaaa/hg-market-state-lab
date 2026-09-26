"""Source Capture ``mo_option_basic``: the active MO contract facts of one date.

Source: Tushare ``opt_basic`` (see ``capture/ARCHITECTURE.md`` section 5;
the product universe is in ``products/csi1000_5d_analysis/data.md`` section 4.1).

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``services/delivery.md`` section 4):

    poetry run python -m market_snapshot.capture.mo_option_basic 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common

RAW_ARTIFACT = "mo_option_basic"
# Capture scope of the MO chain (Guide 5.1). These limits select the Capture
# scope, not an analysis subset.
EXCHANGE = "CFFEX"
PRODUCT = "MO"
# ``opt_basic.opt_code`` is the underlying index of the option in Source form
# (``OP`` + index code), not the exchange product code: the CSI1000 MO options
# carry ``OP000852.SH`` (000852.SH, the CSI1000 index of this scenario), while
# the other CFFEX products carry their own index (``OP000300.SH`` for IO,
# ``OP000016.SH`` for HO).
MO_OPTIONS_CODE = "OP000852.SH"


def query_opt_basic(api: tushare.TushareApi, exchange: str) -> pd.DataFrame:
    """Read the CFFEX option contract facts from Tushare ``opt_basic``.

    ``opt_basic`` has no product parameter, so the product limit below is
    applied to the returned Source facts.
    """
    return api.opt_basic(exchange=exchange)


def is_mo_option(record: artifacts.RawRecord) -> bool:
    """Report whether a CFFEX option contract fact belongs to the MO product.

    ``opt_basic`` identifies the option product by its underlying index
    (``OP000852.SH`` for the CSI1000 MO options), which is the Source fact that
    decides product membership; the contract name is not used, so the check stays
    independent of naming conventions.
    """
    return str(record.get("opt_code") or "") == MO_OPTIONS_CODE


def require_mo_lifecycle(record: artifacts.RawRecord) -> tuple[str, str]:
    """Return the ``(list_date, delist_date)`` a MO contract fact needs.

    A contract fact that is already a member of the MO Capture scope but carries
    no usable lifecycle fact cannot be placed on a trade date at all. The Source
    fact is incomplete, so this fails instead of treating the contract as
    active, dropping it, or inferring a bound. An inverted lifecycle is invalid
    for the same reason.
    """
    list_date = tushare.to_iso_date_or_none(record.get("list_date"))
    delist_date = tushare.to_iso_date_or_none(record.get("delist_date"))
    if list_date is None or delist_date is None:
        raise common.CollectionError(
            f"{PRODUCT} contract {record.get('ts_code')} of exchange={EXCHANGE} has no "
            f"usable lifecycle facts in Tushare opt_basic "
            f"(list_date={record.get('list_date')!r}, "
            f"delist_date={record.get('delist_date')!r})."
        )
    if delist_date < list_date:
        raise common.CollectionError(
            f"{PRODUCT} contract {record.get('ts_code')} has delist_date={delist_date} "
            f"before list_date={list_date}."
        )
    return list_date, delist_date


def lifecycle_covers(record: artifacts.RawRecord, trade_date: str) -> bool:
    """Apply the Source-fact lifecycle rule ``list_date <= date <= delist_date``."""
    list_date, delist_date = require_mo_lifecycle(record)
    return list_date <= trade_date <= delist_date


def select_active_mo_universe(
    facts: Sequence[artifacts.RawRecord], trade_date: str
) -> list[artifacts.RawRecord]:
    """Return the active MO option contract facts of one trade date.

    ``facts`` are the normalized ``opt_basic`` contract facts of this Capture
    (the Capture scope ``exchange`` / product is decided before the lifecycle
    check), so a member contract with incomplete lifecycle facts fails instead of
    disappearing from the universe.
    """
    members = [
        record
        for record in facts
        if str(record.get("exchange") or "") == EXCHANGE and is_mo_option(record)
    ]
    return [record for record in members if lifecycle_covers(record, trade_date)]


def collect_mo_option_basic(
    trade_date: str, query: common.QueryFunc
) -> list[artifacts.RawRecord]:
    """Return the ``mo_option_basic`` records for the given trade date.

    The Capture scope is the whole MO / CFFEX contract universe of the Source
    response; the lifecycle rule selects the active part of it.
    """
    # Reject a malformed project-level date before any Source request.
    tushare.to_tushare_date(trade_date)
    records = select_active_mo_universe(
        common.to_raw_records(query(exchange=EXCHANGE)), trade_date
    )

    if not records:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no active {PRODUCT} contract on "
            f"trade_date={trade_date}."
        )

    records.sort(key=lambda record: str(record["ts_code"]))
    return records


def capture(api: tushare.TushareApi, trade_date: str) -> list[artifacts.RawRecord]:
    """Run this Source Capture for one target trade date against a Source api.

    ``opt_basic`` has no product parameter, so the product limit is applied to
    the returned Source facts inside this module; a caller (the Data Service or
    the development entrypoint) only asks for the Capture
    (``ARCHITECTURE.md`` 2).
    """
    return collect_mo_option_basic(
        trade_date, lambda **kwargs: query_opt_basic(api, **kwargs)
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
