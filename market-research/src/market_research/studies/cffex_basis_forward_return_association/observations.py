"""Construct the three independent Study Observations from public Snapshot results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
)

from .context import FAMILIES, HORIZONS, PREDICTOR, SLOTS, CFFEXStudyError
from .statistics import _finite, _mean


def _artifact_identity(
    name: str, snapshots: dict[str, CFFEXEquityIndexBasisHistoryResult]
) -> dict[str, Any]:
    def public_input_digest(snapshot: CFFEXEquityIndexBasisHistoryResult) -> str:
        digest = hashlib.sha256()
        for observation in snapshot.observations:
            digest.update(
                json.dumps(
                    asdict(observation),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
            )
            digest.update(b"\n")
        return digest.hexdigest()

    descriptor: dict[str, Any] = {
        "component": name,
        "inputs": [
            {
                "family": family,
                "start_trade_date": snapshots[family].start_trade_date,
                "effective_start_trade_date": max(
                    snapshots[family].start_trade_date, snapshots[family].family_listing_date
                ),
                "end_trade_date": snapshots[family].end_trade_date,
                "underlying_code": snapshots[family].underlying_code,
                "source_identity": snapshots[family].source_identity,
                "public_input_sha256": public_input_digest(snapshots[family]),
            }
            for family in FAMILIES
        ],
    }
    if name == "daily_basis_environment":
        descriptor["calculation"] = PREDICTOR
    if name == "underlying_forward_returns":
        descriptor["horizons"] = list(HORIZONS)
        descriptor["future_support_end_trade_date"] = snapshots["IF"].end_trade_date
    canonical = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "semantic_inputs": descriptor,
    }


def build(snapshots: dict[str, CFFEXEquityIndexBasisHistoryResult]) -> dict[str, Any]:
    """Build basis term structure, daily environment and forward return paths."""
    term: list[dict[str, Any]] = []
    daily_basis: list[dict[str, Any]] = []
    returns: list[dict[str, Any]] = []
    by_family: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        snapshot = snapshots[family]
        by_date: dict[str, dict[str, Any]] = {}
        for observation in snapshot.observations:
            if (
                observation.futures_family != family
                or observation.underlying_code != snapshot.underlying_code
            ):
                raise CFFEXStudyError("Snapshot observation family or underlying mismatch.")
            day = by_date.setdefault(observation.trade_date, {})
            if observation.contract_slot not in SLOTS or observation.contract_slot in day:
                raise CFFEXStudyError("Snapshot contains duplicate or unknown contract slot.")
            day[observation.contract_slot] = observation
        if not by_date:
            raise CFFEXStudyError(f"{family} has no basis history.")
        basis_rows: list[dict[str, Any]] = []
        return_rows: list[dict[str, Any]] = []
        term_rows: list[dict[str, Any]] = []
        dates = sorted(by_date)
        closes: list[float] = []
        for trade_date in dates:
            slots = by_date[trade_date]
            if set(slots) != set(SLOTS):
                raise CFFEXStudyError(f"{family} has incomplete slots on {trade_date}.")
            close = _finite(slots["M0"].underlying_close, "underlying close")
            if close == 0 or any(
                _finite(row.underlying_close, "underlying close") != close for row in slots.values()
            ):
                raise CFFEXStudyError("Snapshot underlying closes are inconsistent.")
            closes.append(close)
            for slot in SLOTS:
                contract_row = slots[slot]
                _finite(contract_row.annualized_basis_pct, "annualized basis")
                term_row = {"family": family, **asdict(contract_row)}
                term.append(term_row)
                term_rows.append(term_row)
            component = {
                slot: _finite(slots[slot].annualized_basis_pct, "annualized basis")
                for slot in ("M1", "Q1", "Q2")
            }
            predictor = _mean(list(component.values()))
            basis_row = {
                "family": family,
                "trade_date": trade_date,
                "daily_non_front_basis": predictor,
                **{f"{slot.lower()}_annualized_basis_pct": component[slot] for slot in component},
            }
            basis_rows.append(basis_row)
            daily_basis.append(basis_row)
        for index, trade_date in enumerate(dates):
            row: dict[str, Any] = {
                "family": family,
                "trade_date": trade_date,
                "underlying_close": closes[index],
            }
            for horizon in HORIZONS:
                row[f"forward_return_{horizon}d_pct"] = (
                    _finite((closes[index + horizon] / closes[index] - 1) * 100, "forward return")
                    if index + horizon < len(dates)
                    else None
                )
            return_rows.append(row)
            returns.append(row)
        by_family[family] = {"term": term_rows, "basis": basis_rows, "returns": return_rows}
    return {
        "basis_term_structure": term,
        "daily_basis_environment": daily_basis,
        "underlying_forward_returns": returns,
        "by_family": by_family,
        "identities": {
            name: _artifact_identity(name, snapshots)
            for name in (
                "basis_term_structure",
                "daily_basis_environment",
                "underlying_forward_returns",
            )
        },
    }
