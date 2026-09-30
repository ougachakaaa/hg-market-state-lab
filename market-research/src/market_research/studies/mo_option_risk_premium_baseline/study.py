"""Compose the MO option baseline Observation, Analyses, and evidence result."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from market_snapshot.products.index_daily_history import IndexDailyHistoryResult
from market_snapshot.products.mo_option_chain.service import OptionChain

from . import analyses, observations, provenance
from .inputs import STUDY_ID as STUDY_ID
from .inputs import MOOptionRiskPremiumRequest as MOOptionRiskPremiumRequest
from .inputs import MOOptionRiskPremiumStudyError as MOOptionRiskPremiumStudyError
from .inputs import canonical_request as canonical_request
from .inputs import chain_query as chain_query
from .inputs import decimal_text as decimal_text
from .inputs import index_request as index_request
from .inputs import run_key as run_key
from .observations import OutcomeCell as OutcomeCell
from .observations import SnapshotContractError as SnapshotContractError


@dataclass(frozen=True)
class StudyResult:
    request: MOOptionRiskPremiumRequest
    run_key: str
    cells: tuple[OutcomeCell, ...]
    summary: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]
    expected_expiry_count: int


def compute(
    request: MOOptionRiskPremiumRequest,
    index: IndexDailyHistoryResult,
    chains: Mapping[str, tuple[OptionChain, OptionChain]],
) -> StudyResult:
    """Compose the named Observation and two Analysis views from public facts."""
    cells, expiry_count = observations.build_panel(request, index, chains)
    summary = analyses._summarize(cells, request, expiry_count)
    source_provenance = provenance.build_provenance(request, index, chains, cells)
    return StudyResult(request, run_key(request), cells, summary, source_provenance, expiry_count)
