"""Assemble the analysis-ready CSI1000 5-day analysis Snapshot.

Definition authority: ``guides/csi1000-5d-analysis-snapshot.md``.

Input (read-only, no network, no fallback):

    data/raw/csi1000-5d-analysis/<target_trade_date>/
        index_daily_history.json
        mo_option_basic.json
        mo_option_daily.json
        im_futures_basic.json
        im_futures_daily.json

Output:

    data/snapshots/csi1000-5d-analysis/<target_trade_date>/snapshot.json

Usage:
    poetry run python scripts/build_snapshot.py 2026-09-17
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
from _common import CSI1000_RAW_SUBDIR, RAW_DIR, SNAPSHOTS_DIR  # noqa: E402

# Guide section 10: one JSON file per target trade date.
SNAPSHOT_FILENAME = "snapshot.json"

# Guide 4/5: the CSI1000 identity of the ``underlying`` section.
UNDERLYING_TS_CODE = "000852.SH"

# Guide 5.1: exactly this many distinct trading rows end at the target date.
UNDERLYING_HISTORY_DAYS = 120
# Guide 8.2: the IM analysis window is the last 60 dates of that history.
IM_WINDOW_DAYS = 60
# Guide 6.4: the ATR mean uses the most recent 14 True Ranges.
ATR_WINDOW = 14
# Guide 6.5: trading days per year used to annualize realized volatility.
TRADING_DAYS_PER_YEAR = 252
# Guide 8.4: calendar days per year used to annualize the futures basis.
CALENDAR_DAYS_PER_YEAR = 365

# Guide 5.2 / 8.3: Raw Fact fields of the snapshot copy, in output order.
UNDERLYING_HISTORY_FIELDS = (
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount",
)
MO_RAW_FIELDS = ("open", "high", "low", "close", "settle", "vol", "amount", "oi")
IM_RAW_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "settle",
    "vol",
    "amount",
    "oi",
    "oi_chg",
)

# The five Raw artifacts of ``guides/csi1000-5d-analysis-data.md`` section 7.
INDEX_HISTORY_DATASET = "index_daily_history"
MO_BASIC_DATASET = "mo_option_basic"
MO_DAILY_DATASET = "mo_option_daily"
IM_BASIC_DATASET = "im_futures_basic"
IM_DAILY_DATASET = "im_futures_daily"

RawRecord = dict[str, Any]


class SnapshotError(Exception):
    """Raised when the Snapshot cannot be assembled as the Guide requires."""


def to_iso_date(value: Any, field: str) -> str:
    """Normalize one Source contract date fact to ``YYYY-MM-DD``.

    ``mo_option_basic.maturity_date`` is still written as ``YYYYMMDD`` by the
    Goal 2 Collector (see Guide 16), so both the Source form and an already
    normalized Raw value are accepted; anything else fails.
    """
    if value is None:
        raise SnapshotError(f"required {field} is missing: {value!r}.")
    try:
        iso_date = _common.to_iso_date_or_none(value)
    except _common.CollectionError as exc:
        raise SnapshotError(f"{field} is not a usable date: {value!r}.") from exc
    if iso_date is None:
        raise SnapshotError(f"required {field} is missing: {value!r}.")
    return iso_date


def require_text(record: RawRecord, field: str) -> str:
    """Return a required non-empty string field."""
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{field} must be a non-empty string, got {value!r}.")
    return value


def require_number(record: RawRecord, field: str) -> float | int:
    """Return a required finite number field.

    ``bool`` is rejected even though it is an ``int``, and ``None`` / strings /
    NaN / infinities fail: a malformed Raw fact must never reach a derived
    formula. The number itself is kept as it was read, so the snapshot does not
    change an integer Raw fact into a float.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SnapshotError(f"{field} must be a number, got {value!r}.")
    if not math.isfinite(value):
        raise SnapshotError(f"{field} must be a finite number, got {value!r}.")
    return value


def require_positive_number(record: RawRecord, field: str) -> float | int:
    """Return a required number field that is also strictly positive."""
    value = require_number(record, field)
    if value <= 0:
        raise SnapshotError(f"{field} must be greater than 0, got {value!r}.")
    return value


def require_date(record: RawRecord, field: str) -> str:
    """Return a required ``YYYY-MM-DD`` date field."""
    value = record.get(field)
    if not isinstance(value, str) or not _common.is_iso_date(value):
        raise SnapshotError(f"{field} must use YYYY-MM-DD, got {value!r}.")
    return value


def require_mapping(records: Iterable[RawRecord], dataset: str) -> dict[str, RawRecord]:
    """Index records by ``ts_code``, failing on a missing or duplicate key."""
    mapping: dict[str, RawRecord] = {}
    for record in records:
        code = require_text(record, "ts_code")
        if code in mapping:
            raise SnapshotError(f"{dataset} holds more than one row for ts_code={code}.")
        mapping[code] = record
    return mapping


def require_trade_date(value: str, label: str) -> str:
    """Return a validated ``YYYY-MM-DD`` script-level trade date."""
    if not _common.is_iso_date(value):
        raise SnapshotError(f"{label} must use YYYY-MM-DD, got {value!r}.")
    return value


def load_raw_records(dataset_dir: Path, dataset: str) -> list[RawRecord]:
    """Read one Raw artifact as a list of records, failing on any other shape."""
    path = dataset_dir / f"{dataset}.json"
    if not path.is_file():
        raise SnapshotError(
            f"required Raw artifact is missing: {path}. "
            f"Collect the Raw Datasets of {dataset_dir.name} first."
        )
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"{path} is not valid JSON: {exc}.") from exc
    if not isinstance(payload, list):
        raise SnapshotError(f"{path} must hold a JSON array of Source rows.")
    records: list[RawRecord] = []
    for row in payload:
        if not isinstance(row, dict):
            raise SnapshotError(f"{path} holds a row that is not a JSON object.")
        records.append({str(key): value for key, value in row.items()})
    return records


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean of a non-empty sequence."""
    return math.fsum(values) / len(values)


def sample_std(values: Sequence[float]) -> float:
    """Sample standard deviation with ``ddof=1`` (Guide 6.5).

    Written explicitly rather than delegated to a library default, so the
    ``ddof=1`` convention of the authority is visible at the call site.
    """
    if len(values) < 2:
        raise SnapshotError("sample standard deviation needs at least two values.")
    average = mean(values)
    return math.sqrt(math.fsum((value - average) ** 2 for value in values) / (len(values) - 1))


def percent_change(new: float, old: float) -> float:
    """``(new / old - 1) * 100`` in percentage points."""
    if old == 0:
        raise SnapshotError("percentage change divides by a zero base value.")
    return (new / old - 1) * 100


def true_range(record: RawRecord) -> float:
    """Guide 6.4: ``max(high - low, abs(high - pre_close), abs(low - pre_close))``."""
    high = require_number(record, "high")
    low = require_number(record, "low")
    pre_close = require_number(record, "pre_close")
    return max(high - low, abs(high - pre_close), abs(low - pre_close))


def underlying_history(records: Sequence[RawRecord], target_trade_date: str) -> list[RawRecord]:
    """Select the latest 120 distinct trading rows ending at the target date.

    The window is ``trade_date <= target_trade_date``; anything after the target
    date is not part of the window, and a duplicate ``trade_date`` is a damaged
    Raw artifact rather than a row to skip.
    """
    rows_by_date: dict[str, RawRecord] = {}
    for record in records:
        if record.get("ts_code") != UNDERLYING_TS_CODE:
            raise SnapshotError(
                f"{INDEX_HISTORY_DATASET} returned ts_code={record.get('ts_code')!r} "
                f"for a request of ts_code={UNDERLYING_TS_CODE}."
            )
        trade_date = require_date(record, "trade_date")
        if trade_date in rows_by_date:
            raise SnapshotError(
                f"{INDEX_HISTORY_DATASET} holds duplicate rows for "
                f"ts_code={UNDERLYING_TS_CODE} trade_date={trade_date}."
            )
        rows_by_date[trade_date] = record

    trade_dates = sorted(date for date in rows_by_date if date <= target_trade_date)
    if target_trade_date not in rows_by_date:
        raise SnapshotError(
            f"{INDEX_HISTORY_DATASET} holds no row for ts_code={UNDERLYING_TS_CODE} "
            f"on trade_date={target_trade_date}."
        )
    if len(trade_dates) < UNDERLYING_HISTORY_DAYS:
        raise SnapshotError(
            f"{INDEX_HISTORY_DATASET} holds only {len(trade_dates)} distinct trade dates on "
            f"or before {target_trade_date}, fewer than the "
            f"{UNDERLYING_HISTORY_DAYS} the analysis window needs."
        )
    return [rows_by_date[trade_date] for trade_date in trade_dates[-UNDERLYING_HISTORY_DAYS:]]


def underlying_history_row(record: RawRecord) -> RawRecord:
    """Project one Raw index row onto the Guide 5.2 history fields."""
    row: RawRecord = {"trade_date": require_date(record, "trade_date")}
    for field in UNDERLYING_HISTORY_FIELDS[1:]:
        row[field] = require_number(record, field)
    return row


def underlying_derived(history: Sequence[RawRecord]) -> RawRecord:
    """Evaluate the 11 derived scalars of Guide 6 at the target date."""
    closes = [require_positive_number(record, "close") for record in history]
    log_returns = [
        math.log(closes[index] / closes[index - 1]) for index in range(1, len(closes))
    ]
    return {
        "return_1d_pct": percent_change(closes[-1], closes[-2]),
        "return_5d_pct": percent_change(closes[-1], closes[-6]),
        "return_20d_pct": percent_change(closes[-1], closes[-21]),
        "sma_5": mean(closes[-5:]),
        "sma_20": mean(closes[-20:]),
        "sma_60": mean(closes[-60:]),
        "rolling_high_20": max(
            require_number(record, "high") for record in history[-20:]
        ),
        "rolling_low_20": min(require_number(record, "low") for record in history[-20:]),
        "atr_14": mean([true_range(record) for record in history[-ATR_WINDOW:]]),
        "realized_vol_5d_annualized_pct": sample_std(log_returns[-5:])
        * math.sqrt(TRADING_DAYS_PER_YEAR)
        * 100,
        "realized_vol_20d_annualized_pct": sample_std(log_returns[-20:])
        * math.sqrt(TRADING_DAYS_PER_YEAR)
        * 100,
    }


def load_mo_options(
    dataset_dir: Path, target_trade_date: str, underlying_close: float | int
) -> RawRecord:
    """Assemble the Guide 7 MO option chain from the two MO Raw artifacts."""
    basics = load_raw_records(dataset_dir, MO_BASIC_DATASET)
    dailies = load_raw_records(dataset_dir, MO_DAILY_DATASET)
    basic_by_code = require_mapping(basics, MO_BASIC_DATASET)
    daily_by_code = require_mapping(dailies, MO_DAILY_DATASET)

    unmatched_basic = sorted(set(basic_by_code) - set(daily_by_code))
    unmatched_daily = sorted(set(daily_by_code) - set(basic_by_code))
    if unmatched_basic or unmatched_daily:
        raise SnapshotError(
            f"{MO_BASIC_DATASET} and {MO_DAILY_DATASET} cannot be joined one-to-one on "
            f"ts_code: {len(unmatched_basic)} basic contract(s) without a daily fact "
            f"({', '.join(unmatched_basic[:5])}), {len(unmatched_daily)} daily fact(s) "
            f"without a basic contract ({', '.join(unmatched_daily[:5])})."
        )
    if not basic_by_code:
        raise SnapshotError(f"{MO_BASIC_DATASET} holds no contract for {target_trade_date}.")

    target = date.fromisoformat(target_trade_date)
    chain: list[RawRecord] = []
    for ts_code in sorted(basic_by_code):
        contract = basic_by_code[ts_code]
        daily = daily_by_code[ts_code]
        if daily.get("trade_date") != target_trade_date:
            raise SnapshotError(
                f"{MO_DAILY_DATASET} has trade_date={daily.get('trade_date')!r} for {ts_code}, "
                f"expected {target_trade_date}."
            )
        strike = require_number(contract, "exercise_price")
        expiry_date = to_iso_date(contract.get("maturity_date"), "maturity_date")
        row: RawRecord = {
            "ts_code": ts_code,
            "option_type": require_text(contract, "call_put"),
            "strike": strike,
            "expiry_date": expiry_date,
            "days_to_expiry": (date.fromisoformat(expiry_date) - target).days,
        }
        for field in MO_RAW_FIELDS:
            row[field] = require_number(daily, field)
        row["strike_minus_spot_points"] = strike - underlying_close
        row["moneyness_pct"] = percent_change(strike, underlying_close)
        row["close_premium_pct_of_spot"] = row["close"] / underlying_close * 100
        chain.append(row)

    chain.sort(key=lambda row: (row["expiry_date"], row["strike"], row["option_type"]))
    return {"underlying_close": underlying_close, "chain": chain}


def load_im_futures(
    dataset_dir: Path, target_trade_date: str, underlying: Sequence[RawRecord]
) -> RawRecord:
    """Assemble IM history and the target-date curve (Guide 8 and 9)."""
    basics = load_raw_records(dataset_dir, IM_BASIC_DATASET)
    dailies = load_raw_records(dataset_dir, IM_DAILY_DATASET)
    basic_by_code = require_mapping(basics, IM_BASIC_DATASET)
    if not basic_by_code:
        raise SnapshotError(f"{IM_BASIC_DATASET} holds no contract for {target_trade_date}.")

    # Guide 8.2: the IM window is the last 60 trade dates of the underlying
    # history, so every window trade date has a CSI1000 close by construction.
    window_dates = {str(record["trade_date"]) for record in underlying[-IM_WINDOW_DAYS:]}
    underlying_close_by_date = {str(record["trade_date"]): record["close"] for record in underlying}

    history: list[RawRecord] = []
    for daily in dailies:
        ts_code = require_text(daily, "ts_code")
        trade_date = require_date(daily, "trade_date")
        if trade_date not in window_dates:
            continue
        contract = basic_by_code.get(ts_code)
        if contract is None:
            raise SnapshotError(
                f"{IM_DAILY_DATASET} holds ts_code={ts_code} on trade_date={trade_date}, "
                f"which maps to no known contract in {IM_BASIC_DATASET}."
            )
        delist_date = require_date(contract, "delist_date")
        underlying_close = underlying_close_by_date.get(trade_date)
        if underlying_close is None:
            raise SnapshotError(
                f"{IM_DAILY_DATASET} holds trade_date={trade_date}, which has no matching "
                f"CSI1000 close in the underlying history."
            )
        days_to_delist = (date.fromisoformat(delist_date) - date.fromisoformat(trade_date)).days
        if days_to_delist < 0:
            raise SnapshotError(
                f"{IM_DAILY_DATASET} holds trade_date={trade_date} after delist_date="
                f"{delist_date} of contract {ts_code}."
            )
        close = require_number(daily, "close")

        row: RawRecord = {
            "ts_code": ts_code,
            "trade_date": trade_date,
            "delist_date": delist_date,
            "days_to_delist": days_to_delist,
        }
        for field in IM_RAW_FIELDS:
            row[field] = require_number(daily, field)
        row["underlying_close"] = underlying_close
        row["basis_points"] = close - underlying_close
        row["basis_pct"] = percent_change(close, underlying_close)
        # Guide 8.4: the one defined null is a contract that delists on the
        # observation date, where the linear annualization is undefined.
        row["annualized_basis_pct"] = (
            None
            if days_to_delist == 0
            else row["basis_pct"] * CALENDAR_DAYS_PER_YEAR / days_to_delist
        )
        history.append(row)

    if not history:
        raise SnapshotError(
            f"{IM_DAILY_DATASET} holds no observation inside the last {IM_WINDOW_DAYS} "
            f"trade dates up to {target_trade_date}."
        )

    history.sort(key=lambda row: (row["trade_date"], row["ts_code"]))
    curve = [row for row in history if row["trade_date"] == target_trade_date]
    if not curve:
        raise SnapshotError(
            f"{IM_DAILY_DATASET} holds no observation for trade_date={target_trade_date}, "
            f"so the target-date futures curve would be empty."
        )
    curve.sort(key=lambda row: row["delist_date"])
    return {"history": history, "target_date_curve": curve}


def build_snapshot(trade_date: str) -> RawRecord:
    """Assemble the CSI1000 5-day analysis Snapshot for one target trade date."""
    target_trade_date = require_trade_date(trade_date, "target_trade_date")
    dataset_dir = RAW_DIR / CSI1000_RAW_SUBDIR / target_trade_date

    # Guide 5.3: one target-date close, taken from the underlying history.
    history = underlying_history(
        load_raw_records(dataset_dir, INDEX_HISTORY_DATASET), target_trade_date
    )
    underlying_close = require_positive_number(history[-1], "close")

    mo_options = load_mo_options(dataset_dir, target_trade_date, underlying_close)
    im_futures = load_im_futures(dataset_dir, target_trade_date, history)
    # Guide 5.3: the snapshot carries exactly one target-date close, so the
    # futures curve of that date has to read back the same underlying fact.
    for observation in im_futures["target_date_curve"]:
        if observation["underlying_close"] != underlying_close:
            raise SnapshotError(
                f"target-date close mismatch inside the snapshot: "
                f"{observation['underlying_close']!r} vs {underlying_close!r}."
            )

    return {
        "target_trade_date": target_trade_date,
        "underlying": {
            "ts_code": UNDERLYING_TS_CODE,
            "history": [underlying_history_row(record) for record in history],
            "derived": underlying_derived(history),
        },
        "mo_options": mo_options,
        "im_futures": im_futures,
    }


def write_snapshot(snapshot: RawRecord, trade_date: str) -> Path:
    """Write ``snapshot.json`` and return its path."""
    directory = SNAPSHOTS_DIR / CSI1000_RAW_SUBDIR / trade_date
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / SNAPSHOT_FILENAME
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble the CSI1000 5-day analysis Snapshot from local Raw artifacts."
    )
    parser.add_argument("trade_date", help="Target trade date in YYYY-MM-DD form.")
    args = parser.parse_args(argv)

    try:
        snapshot = build_snapshot(args.trade_date)
        path = write_snapshot(snapshot, args.trade_date)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"wrote snapshot for {snapshot['target_trade_date']} "
        f"({len(snapshot['underlying']['history'])} underlying rows, "
        f"{len(snapshot['mo_options']['chain'])} option contracts, "
        f"{len(snapshot['im_futures']['history'])} futures observations) to {path}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
