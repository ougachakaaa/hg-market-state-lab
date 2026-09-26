"""Source Capture ``index_daily``: the CSI1000 history up to a target trade date.

Source: Tushare ``index_daily`` (see ``capture/ARCHITECTURE.md`` section 3;
the CSI1000 history scope is in ``products/csi1000_5d_analysis/data.md`` sections
5.1 and 6). The Raw artifact is ``index_daily_history.json``; it is not a separate
Source Capture (see the same Guide, section 7).

Development / debugging entrypoint (the Data Service CLI is the canonical user
interface, see ``services/delivery.md`` section 4):

    poetry run python -m market_snapshot.products.csi1000_5d_analysis.capture 2026-09-17
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta

import pandas as pd

from ... import artifacts
from ...capture import common
from ...sources import tushare

RAW_ARTIFACT = "index_daily_history"
# Capture scope of the CSI1000 history window (Guide 4.1).
INDEX_CODE = "000852.SH"
# Implementation detail, not a data contract: the Guide asks for enough Source
# facts to reach the latest 120 trading days, so the Capture requests a
# calendar window that is obviously long enough. The exact window selection
# belongs to Analysis Preparation (Guide 6.1).
LOOKBACK_CALENDAR_DAYS = 240
# Completeness requirement of the same Guide 6.1 window: the Raw artifact must
# let downstream preparation reach the latest 120 *actual* trading days, so at
# least this many distinct trade dates have to be present. The Raw artifact is
# not trimmed to exactly this count.
MIN_HISTORY_TRADE_DATES = 120


def query_index_daily_history(
    api: tushare.TushareApi, ts_code: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Read one index over a calendar window from Tushare ``index_daily``."""
    return api.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def lookback_window(target_trade_date: str) -> tuple[str, str]:
    """Return the requested history window as Source-form ``(start, end)`` dates."""
    end_date = tushare.to_tushare_date(target_trade_date)
    start = datetime.strptime(
        target_trade_date, tushare.TRADE_DATE_ISO_FORMAT
    ) - timedelta(days=LOOKBACK_CALENDAR_DAYS)
    return start.strftime(tushare.TRADE_DATE_TUSHARE_FORMAT), end_date


def require_history_window(
    records: Sequence[artifacts.RawRecord], start_date: str, target_trade_date: str
) -> None:
    """Ensure the history is complete enough for the Guide 6.1 window.

    The history must cover at least ``MIN_HISTORY_TRADE_DATES`` distinct trade
    dates ending at ``target_trade_date``, hold one Source row per trade date,
    and describe only ``INDEX_CODE``. The Raw artifact is not trimmed to that
    count: the exact ``latest 120 trading rows`` selection stays Analysis
    Preparation.
    """
    if not records:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no data for ts_code={INDEX_CODE} "
            f"on or before trade_date={target_trade_date}."
        )

    seen: set[tuple[str, str]] = set()
    for record in records:
        if record.get("ts_code") != INDEX_CODE:
            raise common.CollectionError(
                f"Tushare {RAW_ARTIFACT} returned ts_code={record.get('ts_code')!r} "
                f"for a request of ts_code={INDEX_CODE}."
            )
        in_window = common.in_date_range(
            record, tushare.TRADE_DATE_FIELD, start_date, target_trade_date
        )
        if not in_window:
            raise common.CollectionError(
                f"Tushare {RAW_ARTIFACT} returned {tushare.TRADE_DATE_FIELD}="
                f"{record.get(tushare.TRADE_DATE_FIELD)!r} outside the requested window "
                f"{start_date}..{target_trade_date}."
            )
        key = (str(record["ts_code"]), str(record[tushare.TRADE_DATE_FIELD]))
        if key in seen:
            raise common.CollectionError(
                f"Tushare {RAW_ARTIFACT} returned duplicate rows for ts_code={key[0]} "
                f"trade_date={key[1]}."
            )
        seen.add(key)

    trade_dates = {str(record[tushare.TRADE_DATE_FIELD]) for record in records}
    if target_trade_date not in trade_dates:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned no record for ts_code={INDEX_CODE} "
            f"on trade_date={target_trade_date}."
        )
    if len(trade_dates) < MIN_HISTORY_TRADE_DATES:
        raise common.CollectionError(
            f"Tushare {RAW_ARTIFACT} returned only {len(trade_dates)} distinct "
            f"{tushare.TRADE_DATE_FIELD} values for ts_code={INDEX_CODE}, fewer than the "
            f"{MIN_HISTORY_TRADE_DATES} the analysis window needs."
        )


def collect_index_daily_history(
    trade_date: str, query: common.QueryFunc
) -> list[artifacts.RawRecord]:
    """Return the ``index_daily`` history records of ``000852.SH``.

    The Raw artifact covers a range of trade dates; the window bounds and the
    completeness requirement (at least ``MIN_HISTORY_TRADE_DATES`` distinct
    trade dates ending at the target date) are checked here. Selecting the
    latest 120 trading rows is Analysis Preparation.
    """
    start_date, end_date = lookback_window(trade_date)
    frame = query(ts_code=INDEX_CODE, start_date=start_date, end_date=end_date)
    records = common.to_raw_records(frame)
    source_start = tushare.to_iso_date(start_date)
    records.sort(key=lambda record: record[tushare.TRADE_DATE_FIELD])
    require_history_window(records, source_start, trade_date)
    return records


def capture(api: tushare.TushareApi, trade_date: str) -> list[artifacts.RawRecord]:
    """Run this Source Capture for one target trade date against a Source api.

    The endpoint, its query parameters and the Capture scope stay in this module:
    a caller (the Data Service or the development entrypoint) only asks for the
    Capture, never for a Source endpoint (``ARCHITECTURE.md`` 2).
    """
    return collect_index_daily_history(
        trade_date, lambda **kwargs: query_index_daily_history(api, **kwargs)
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
