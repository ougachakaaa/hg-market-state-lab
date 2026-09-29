"""Compose the CFFEX Study pipeline; authority: studies/.../ARCHITECTURE.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
)

from . import analyses, observations, results
from .context import (
    FAMILIES,
    CFFEXStudyError,
)
from .context import (
    HORIZONS as HORIZONS,
)
from .context import (
    PERCENTILES as PERCENTILES,
)
from .context import (
    PREDICTOR as PREDICTOR,
)
from .context import (
    SLOTS as SLOTS,
)
from .context import (
    STUDY_ID as STUDY_ID,
)


def compute(snapshots_input: list[CFFEXEquityIndexBasisHistoryResult]) -> dict[str, Any]:
    """Validate the Study request, then compose Observations, Analyses and Results."""
    snapshots = {result.futures_family: result for result in snapshots_input}
    if len(snapshots_input) != 4 or set(snapshots) != set(FAMILIES):
        raise CFFEXStudyError("one public Snapshot result is required for each family.")
    start = snapshots["IF"].start_trade_date
    end = snapshots["IF"].end_trade_date
    if any(
        (result.start_trade_date, result.end_trade_date) != (start, end)
        for result in snapshots_input
    ):
        raise CFFEXStudyError("Snapshot request bounds do not match across families.")

    observed = observations.build(snapshots)
    analyzed = analyses.run(observed, snapshots, start, end)
    return results.assemble(snapshots, start, end, observed, analyzed)


def retain(result: dict[str, Any], output_dir: Path) -> tuple[Path, ...]:
    """Retain canonical evidence through the Study Results boundary."""
    return results.retain(result, output_dir)


def run_and_retain(
    snapshots: list[CFFEXEquityIndexBasisHistoryResult], output_dir: Path
) -> dict[str, Any]:
    result = compute(snapshots)
    retain(result, output_dir)
    return result
