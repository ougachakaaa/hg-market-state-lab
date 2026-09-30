"""Full upstream provenance and relevant Observation Artifact identity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from market_snapshot.products.index_daily_history import IndexDailyHistoryResult
from market_snapshot.products.mo_option_chain.service import OptionChain, PriceType

from .inputs import (
    MOOptionRiskPremiumRequest,
    _digest,
    canonical_request,
    chain_query,
    index_request,
)
from .observations import OutcomeCell


def _cell_identity(cell: OutcomeCell) -> dict[str, Any]:
    data = asdict(cell)
    data["exclusion_reasons"] = sorted(set(cell.exclusion_reasons))
    return data


def build_provenance(
    request: MOOptionRiskPremiumRequest,
    index: IndexDailyHistoryResult,
    chains: Mapping[str, tuple[OptionChain, OptionChain]],
    cells: tuple[OutcomeCell, ...],
) -> dict[str, Any]:
    """Retain full source fingerprints; hash only material panel facts for its identity."""
    index_query = index_request(request)
    dates = tuple(row.trade_date for row in index.sample_observations)
    index_facts = asdict(index)
    chain_facts = [asdict(chain) for trade_date in dates for chain in chains[trade_date]]
    result: dict[str, Any] = {
        "index_daily_history": {
            "query": asdict(index_query),
            "content_sha256": _digest(index_facts, sort_keys=True),
        },
        "mo_option_chain": {
            "queries": [
                asdict(chain_query(trade_date, kind))
                for trade_date in dates
                for kind in (PriceType.HIGH, PriceType.LOW)
            ],
            "content_sha256": _digest(chain_facts, sort_keys=True),
        },
    }
    selected_entries = sorted({cell.entry_trade_date for cell in cells if cell.entry_trade_date})
    ordered_cells = sorted(
        cells,
        key=lambda cell: (
            cell.expiry_date,
            cell.target_dte,
            cell.option_type,
            Decimal(cell.moneyness_target),
        ),
    )
    result["observation_artifact_sha256"] = _digest(
        {
            "observation": "ExpiryDteOptionOutcome",
            "request": canonical_request(request),
            "source_queries": {
                "index_daily_history": asdict(index_query),
                "mo_option_chain_selected_entries": [
                    asdict(chain_query(trade_date, kind))
                    for trade_date in selected_entries
                    for kind in (PriceType.HIGH, PriceType.LOW)
                ],
            },
            "cells": [_cell_identity(cell) for cell in ordered_cells],
        },
        sort_keys=True,
    )
    return result
