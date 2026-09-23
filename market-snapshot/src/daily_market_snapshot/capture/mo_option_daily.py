"""Source Capture ``mo_option_daily``: daily facts of the active MO universe.

Source: Tushare ``opt_daily`` (see ``market-snapshot/guides/source-captures.md`` section 6;
the product universe is in ``market-snapshot/guides/csi1000-5d-analysis/data.md`` section 4.1).
``exchange=CFFEX`` only asks the Source for CFFEX option daily facts;
the Capture scope is then decided by the active MO universe the
``mo_option_basic`` Capture has already collected for the same request, so other
CFFEX option products (IO, HO) are simply not in scope. Only the daily facts of
that universe belong to this Raw Artifact.

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``market-snapshot/guides/data-services.md`` section 4):

    poetry run python -m daily_market_snapshot.capture.mo_option_daily 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import pandas as pd

from .. import artifacts
from ..sources import tushare
from . import common, mo_option_basic

EXCHANGE = mo_option_basic.EXCHANGE
PRODUCT = mo_option_basic.PRODUCT
RAW_ARTIFACT = "mo_option_daily"


def query_opt_daily(
    api: tushare.TushareApi, trade_date: str, exchange: str
) -> pd.DataFrame:
    """Read one trade date of CFFEX option quotes from Tushare ``opt_daily``."""
    return api.opt_daily(trade_date=trade_date, exchange=exchange)


def collect_mo_option_daily(
    trade_date: str,
    basic_facts: Sequence[artifacts.RawRecord],
    query: common.QueryFunc,
) -> list[artifacts.RawRecord]:
    """Return the ``mo_option_daily`` records of the active MO universe.

    ``basic_facts`` are the contract facts the ``mo_option_basic`` Capture
    collected for this request; the daily Capture reuses them for its own scope
    instead of asking the Source for the same contract facts a second time. The
    ``opt_daily`` response is filtered down to that universe, and the surviving
    rows must match it exactly: every active contract needs its daily fact, and
    no contract may repeat.
    """
    tushare_date = tushare.to_tushare_date(trade_date)
    universe = mo_option_basic.select_active_mo_universe(basic_facts, trade_date)
    if not universe:
        raise common.CollectionError(
            f"no active {PRODUCT} contract on trade_date={trade_date}; "
            f"{RAW_ARTIFACT} needs the active universe from the mo_option_basic Capture."
        )
    active_codes = {str(record["ts_code"]) for record in universe}

    frame = query(trade_date=tushare_date, exchange=EXCHANGE)
    records = common.to_raw_records(frame)
    if not records:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no data for trade_date={trade_date}."
        )
    common.require_target_trade_date(records, trade_date)

    # ``exchange=CFFEX`` also returns other option products; they are not in this
    # Capture scope and are excluded, not failed on.
    members = [record for record in records if record.get("ts_code") in active_codes]

    seen: set[str] = set()
    for record in members:
        code = str(record["ts_code"])
        if code in seen:
            raise common.CollectionError(
                f"Tushare {RAW_ARTIFACT} returned more than one row for active {PRODUCT} "
                f"contract {code} on trade_date={trade_date}."
            )
        seen.add(code)

    missing = sorted(active_codes - seen)
    if missing:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no daily row for {len(missing)} active "
            f"{PRODUCT} contract(s) on trade_date={trade_date}: {', '.join(missing[:5])}."
        )

    members.sort(key=lambda record: str(record["ts_code"]))
    return members


def capture(
    api: tushare.TushareApi, trade_date: str, basic_facts: Sequence[artifacts.RawRecord]
) -> list[artifacts.RawRecord]:
    """Run this Source Capture, reusing the MO basic facts of the same request.

    The endpoint and its query parameters stay in this module; the Capture scope
    comes from the ``mo_option_basic`` Capture facts the caller passes in
    (``ARCHITECTURE.md`` 2).
    """
    return collect_mo_option_daily(
        trade_date, basic_facts, lambda **kwargs: query_opt_daily(api, **kwargs)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Collect the {RAW_ARTIFACT} Raw artifact.")
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
        basic_facts = mo_option_basic.capture(api, args.trade_date)
        records = capture(api, args.trade_date, basic_facts)
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
