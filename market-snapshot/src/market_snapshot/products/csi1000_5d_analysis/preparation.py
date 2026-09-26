"""Analysis Preparation: the CSI1000 5-day analysis analysis-ready artifact.

Definition authority: ``products/csi1000_5d_analysis/preparation-contract.md``.

Input (read-only, local Raw artifacts only; no network, no fallback):

    data/raw/csi1000-5d-analysis/<target_trade_date>/
        index_daily_history.json
        mo_option_basic.json
        mo_option_daily.json
        im_futures_basic.json
        im_futures_daily.json

Output: the analysis-ready payload the Data Service publishes as

    output/csi1000-5d-analysis/<target_trade_date>/snapshot.json

This module performs the deterministic preparation only: it never calls Tushare,
never accesses the network and never publishes to the output root. Running the
Data Service CLI is the canonical way to produce the artifact
(``poetry run python market-snapshot/scripts/dms.py get csi1000-5d-analysis --date ...``).

Missing Source facts: a quote field that only gets copied onto the artifact and
feeds no derived formula (``open`` / ``high`` / ``low`` of a contract that did
not trade, ``oi_chg`` of an observation on its first trading day) stays ``null``
when the Source did not return it, instead of failing the preparation. Every
field a derived formula reads (``close`` in particular) must still be present
and well formed, or the preparation fails.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from ... import artifacts
from ...artifacts import RawRecord
from ...sources import tushare

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

# Guide 5.2: Raw Fact fields of the underlying history copy, in output order.
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

# Guide 5.1 / 8.3: the quote fields the artifact copies straight from the Source
# fact without reading them into any derived formula. ``close`` is deliberately
# absent: it feeds ``close_premium_pct_of_spot`` (MO) and the basis fields (IM),
# so it is a required derived input, read once with ``require_number`` instead of
# passing through as a possibly-missing fact.
MO_PASSTHROUGH_FIELDS = ("open", "high", "low", "settle", "vol", "amount", "oi")
IM_PASSTHROUGH_FIELDS = (
    "open",
    "high",
    "low",
    "settle",
    "vol",
    "amount",
    "oi",
    "oi_chg",
)

# The five Raw artifacts of ``products/csi1000_5d_analysis/data.md`` section 6.
INDEX_HISTORY_RAW_ARTIFACT = "index_daily_history"
MO_BASIC_RAW_ARTIFACT = "mo_option_basic"
MO_DAILY_RAW_ARTIFACT = "mo_option_daily"
IM_BASIC_RAW_ARTIFACT = "im_futures_basic"
IM_DAILY_RAW_ARTIFACT = "im_futures_daily"


class SnapshotError(Exception):
    """Raised when the analysis-ready artifact cannot be prepared as required."""


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
    formula. The number itself is kept as it was read, so the artifact does not
    change an integer Raw fact into a float.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SnapshotError(f"{field} must be a number, got {value!r}.")
    if not math.isfinite(value):
        raise SnapshotError(f"{field} must be a finite number, got {value!r}.")
    return value


def passthrough_fields(record: RawRecord, fields: tuple[str, ...]) -> RawRecord:
    """Project quote fields the artifact only copies onto a row.

    None of these fields feeds a required derived formula, so a value the Source
    did not return stays ``null`` in the artifact instead of failing the
    preparation: a contract that did not trade has no ``open`` / ``high`` /
    ``low``, and an observation on its first trading day has no ``oi_chg``. The
    missing fact is preserved as missing rather than filled in, and a value that
    is present but malformed (a string, NaN, an infinity) still fails.

    Only the nullable pass-through fields named by the caller belong here;
    ``close`` is a required derived input and is therefore read once with
    ``require_number`` at the call site instead.
    """
    row: RawRecord = {}
    for field in fields:
        value: Any = record.get(field)
        row[field] = None if value is None else require_number(record, field)
    return row


def require_positive_number(record: RawRecord, field: str) -> float | int:
    """Return a required number field that is also strictly positive."""
    value = require_number(record, field)
    if value <= 0:
        raise SnapshotError(f"{field} must be greater than 0, got {value!r}.")
    return value


def require_date(record: RawRecord, field: str) -> str:
    """Return a required ``YYYY-MM-DD`` date field."""
    value = record.get(field)
    if not isinstance(value, str) or not tushare.is_iso_date(value):
        raise SnapshotError(f"{field} must use YYYY-MM-DD, got {value!r}.")
    return value


def require_mapping(records: Iterable[RawRecord], raw_artifact: str) -> dict[str, RawRecord]:
    """Index records by ``ts_code``, failing on a missing or duplicate key."""
    mapping: dict[str, RawRecord] = {}
    for record in records:
        code = require_text(record, "ts_code")
        if code in mapping:
            raise SnapshotError(f"{raw_artifact} holds more than one row for ts_code={code}.")
        mapping[code] = record
    return mapping


def require_trade_date(value: str, label: str) -> str:
    """Return a validated ``YYYY-MM-DD`` project-level trade date."""
    if not tushare.is_iso_date(value):
        raise SnapshotError(f"{label} must use YYYY-MM-DD, got {value!r}.")
    return value


def load_raw_records(raw_dir: Path, raw_artifact: str) -> list[RawRecord]:
    """Read one Raw artifact as a list of records, failing on any other shape."""
    path = raw_dir / f"{raw_artifact}.json"
    if not path.is_file():
        raise SnapshotError(
            f"required Raw artifact is missing: {path}. "
            f"Collect the Raw Artifacts of {raw_dir.name} first."
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
                f"{INDEX_HISTORY_RAW_ARTIFACT} returned ts_code={record.get('ts_code')!r} "
                f"for a request of ts_code={UNDERLYING_TS_CODE}."
            )
        trade_date = require_date(record, "trade_date")
        if trade_date in rows_by_date:
            raise SnapshotError(
                f"{INDEX_HISTORY_RAW_ARTIFACT} holds duplicate rows for "
                f"ts_code={UNDERLYING_TS_CODE} trade_date={trade_date}."
            )
        rows_by_date[trade_date] = record

    trade_dates = sorted(date for date in rows_by_date if date <= target_trade_date)
    if target_trade_date not in rows_by_date:
        raise SnapshotError(
            f"{INDEX_HISTORY_RAW_ARTIFACT} holds no row for ts_code={UNDERLYING_TS_CODE} "
            f"on trade_date={target_trade_date}."
        )
    if len(trade_dates) < UNDERLYING_HISTORY_DAYS:
        raise SnapshotError(
            f"{INDEX_HISTORY_RAW_ARTIFACT} holds only {len(trade_dates)} distinct trade dates on "
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
    raw_dir: Path, target_trade_date: str, underlying_close: float | int
) -> RawRecord:
    """Assemble the Guide 7 MO option chain from the two MO Raw artifacts."""
    basics = load_raw_records(raw_dir, MO_BASIC_RAW_ARTIFACT)
    dailies = load_raw_records(raw_dir, MO_DAILY_RAW_ARTIFACT)
    basic_by_code = require_mapping(basics, MO_BASIC_RAW_ARTIFACT)
    daily_by_code = require_mapping(dailies, MO_DAILY_RAW_ARTIFACT)

    unmatched_basic = sorted(set(basic_by_code) - set(daily_by_code))
    unmatched_daily = sorted(set(daily_by_code) - set(basic_by_code))
    if unmatched_basic or unmatched_daily:
        raise SnapshotError(
            f"{MO_BASIC_RAW_ARTIFACT} and {MO_DAILY_RAW_ARTIFACT} cannot be joined one-to-one on "
            f"ts_code: {len(unmatched_basic)} basic contract(s) without a daily fact "
            f"({', '.join(unmatched_basic[:5])}), {len(unmatched_daily)} daily fact(s) "
            f"without a basic contract ({', '.join(unmatched_daily[:5])})."
        )
    if not basic_by_code:
        raise SnapshotError(f"{MO_BASIC_RAW_ARTIFACT} holds no contract for {target_trade_date}.")

    target = date.fromisoformat(target_trade_date)
    chain: list[RawRecord] = []
    for ts_code in sorted(basic_by_code):
        contract = basic_by_code[ts_code]
        daily = daily_by_code[ts_code]
        if daily.get("trade_date") != target_trade_date:
            raise SnapshotError(
                f"{MO_DAILY_RAW_ARTIFACT} has trade_date={daily.get('trade_date')!r} "
                f"for {ts_code}, expected {target_trade_date}."
            )
        strike = require_number(contract, "exercise_price")
        expiry_date = require_date(contract, "maturity_date")
        # ``close`` feeds ``close_premium_pct_of_spot``, so it is a required
        # derived input: a missing or malformed close must fail here instead of
        # passing through as ``null``.
        close = require_number(daily, "close")
        row: RawRecord = {
            "ts_code": ts_code,
            "option_type": require_text(contract, "call_put"),
            "strike": strike,
            "expiry_date": expiry_date,
            "days_to_expiry": (date.fromisoformat(expiry_date) - target).days,
        }
        # Guide 7.3 output order lists the quote fields as open, high, low,
        # close, settle, vol, amount, oi: the nullable pass-through groups sit
        # around the required close.
        row.update(passthrough_fields(daily, MO_PASSTHROUGH_FIELDS[:3]))
        row["close"] = close
        row.update(passthrough_fields(daily, MO_PASSTHROUGH_FIELDS[3:]))
        row["strike_minus_spot_points"] = strike - underlying_close
        row["moneyness_pct"] = percent_change(strike, underlying_close)
        row["close_premium_pct_of_spot"] = close / underlying_close * 100
        chain.append(row)

    chain.sort(key=lambda row: (row["expiry_date"], row["strike"], row["option_type"]))
    return {"underlying_close": underlying_close, "chain": chain}


def load_im_futures(
    raw_dir: Path, target_trade_date: str, underlying: Sequence[RawRecord]
) -> RawRecord:
    """Assemble IM history and the target-date curve (Guide 8 and 9)."""
    basics = load_raw_records(raw_dir, IM_BASIC_RAW_ARTIFACT)
    dailies = load_raw_records(raw_dir, IM_DAILY_RAW_ARTIFACT)
    basic_by_code = require_mapping(basics, IM_BASIC_RAW_ARTIFACT)
    if not basic_by_code:
        raise SnapshotError(f"{IM_BASIC_RAW_ARTIFACT} holds no contract for {target_trade_date}.")

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
                f"{IM_DAILY_RAW_ARTIFACT} holds ts_code={ts_code} on trade_date={trade_date}, "
                f"which maps to no known contract in {IM_BASIC_RAW_ARTIFACT}."
            )
        delist_date = require_date(contract, "delist_date")
        underlying_close = underlying_close_by_date.get(trade_date)
        if underlying_close is None:
            raise SnapshotError(
                f"{IM_DAILY_RAW_ARTIFACT} holds trade_date={trade_date}, which has no matching "
                f"CSI1000 close in the underlying history."
            )
        days_to_delist = (date.fromisoformat(delist_date) - date.fromisoformat(trade_date)).days
        if days_to_delist < 0:
            raise SnapshotError(
                f"{IM_DAILY_RAW_ARTIFACT} holds trade_date={trade_date} after delist_date="
                f"{delist_date} of contract {ts_code}."
            )
        close = require_number(daily, "close")

        row: RawRecord = {
            "ts_code": ts_code,
            "trade_date": trade_date,
            "delist_date": delist_date,
            "days_to_delist": days_to_delist,
        }
        # Guide 8.3 output order lists the quote fields as open, high, low,
        # close, settle, vol, amount, oi, oi_chg: the nullable pass-through
        # groups sit around the required close, which is read once above.
        row.update(passthrough_fields(daily, IM_PASSTHROUGH_FIELDS[:3]))
        row["close"] = close
        row.update(passthrough_fields(daily, IM_PASSTHROUGH_FIELDS[3:]))
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
            f"{IM_DAILY_RAW_ARTIFACT} holds no observation inside the last {IM_WINDOW_DAYS} "
            f"trade dates up to {target_trade_date}."
        )

    history.sort(key=lambda row: (row["trade_date"], row["ts_code"]))
    curve = [row for row in history if row["trade_date"] == target_trade_date]
    if not curve:
        raise SnapshotError(
            f"{IM_DAILY_RAW_ARTIFACT} holds no observation for trade_date={target_trade_date}, "
            f"so the target-date futures curve would be empty."
        )
    curve.sort(key=lambda row: row["delist_date"])
    return {"history": history, "target_date_curve": curve}


def build_snapshot(trade_date: str, raw_dir: Path | None = None) -> RawRecord:
    """Prepare the CSI1000 5-day analysis artifact for one target trade date.

    ``raw_dir`` defaults to the Raw directory of ``trade_date`` under
    :data:`artifacts.RAW_DIR`; the Data Service passes the directory it collected
    into, and a test can pass a temporary one.
    """
    target_trade_date = require_trade_date(trade_date, "target_trade_date")
    if raw_dir is None:
        raw_dir = artifacts.csi1000_raw_dir(target_trade_date)

    # Guide 5.3: one target-date close, taken from the underlying history.
    history = underlying_history(
        load_raw_records(raw_dir, INDEX_HISTORY_RAW_ARTIFACT), target_trade_date
    )
    underlying_close = require_positive_number(history[-1], "close")

    mo_options = load_mo_options(raw_dir, target_trade_date, underlying_close)
    im_futures = load_im_futures(raw_dir, target_trade_date, history)
    # Guide 5.3: the artifact carries exactly one target-date close, so the
    # futures curve of that date has to read back the same underlying fact.
    for observation in im_futures["target_date_curve"]:
        if observation["underlying_close"] != underlying_close:
            raise SnapshotError(
                f"target-date close mismatch inside the artifact: "
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
