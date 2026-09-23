"""Data Service ``csi1000-5d-analysis``: orchestration of the whole chain.

Authority: ``market-snapshot/guides/data-services.md`` (Data Service catalogue, CLI contract,
canonical output) over ``market-snapshot/guides/csi1000-5d-analysis/data.md`` (Raw Artifacts) and
``market-snapshot/guides/csi1000-5d-analysis/preparation.md`` (Analysis Preparation Definition).

The Data Service owns orchestration only: it runs the required Source Captures in
order, writes their Raw Artifacts, calls the deterministic Analysis Preparation
and publishes the canonical analysis-ready artifact. It redefines neither Source
Capture semantics nor Preparation formulas, and it names no Source endpoint and
no Capture query parameter: each Capture owns its own Source call
(``ARCHITECTURE.md`` 2).

Canonical output:

    output/csi1000-5d-analysis/<target_trade_date>/snapshot.json
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from .. import artifacts
from ..capture import common as capture_common
from ..capture import (
    csi1000_index_history,
    im_futures_basic,
    im_futures_daily,
    mo_option_basic,
    mo_option_daily,
)
from ..preparation import csi1000_5d_analysis as preparation
from ..sources import tushare
from . import DataServiceError

# The Analysis Preparation module, reached through a binding so this service can
# be tested against a patched Preparation.
_preparation: ModuleType = preparation

SERVICE_ID = artifacts.CSI1000_RAW_SUBDIR
SERVICE_DESCRIPTION = (
    "analysis-ready data product for an external analyzer of the CSI1000 "
    "market state over the next ~5 trading days"
)


def run_capture_stage(
    name: str,
    raw_artifact: str,
    raw_dir: Path,
    capture: Callable[[], list[artifacts.RawRecord]],
) -> list[artifacts.RawRecord]:
    """Run one Capture stage and write its Raw Artifact.

    A Capture that raises a collection failure is reported as the failed stage
    and stops the chain, so no later Capture runs and no Analysis Preparation
    runs. The captured records are returned, so a later stage of the same request
    can reuse the Source facts this Capture already read.
    """
    try:
        records = capture()
    except capture_common.CAPTURE_FAILURE_TYPES as exc:
        raise DataServiceError(f"stage={name} error={exc}") from exc
    artifacts.write_raw_artifact(records, raw_dir, raw_artifact)
    return records


def collect_csi1000_5d_analysis(
    api: tushare.TushareApi, target_trade_date: str, raw_root: Path
) -> Path:
    """Run the five CSI1000 analysis Source Captures for one target trade date.

    Authority order (``market-snapshot/guides/data-services.md`` section 5):

        CSI1000 history -> MO option basic -> MO option daily ->
        IM futures basic -> IM futures daily

    Each Capture writes its own Raw Artifact, and one Capture runs at a time: a
    failing stage stops the chain before any later Capture runs, so a failure
    also leaves no Analysis Preparation and no final output.

    The MO and IM basic Captures also carry the contract facts their own daily
    Capture needs for its scope. Those facts are reused here, so each basic
    Capture reads the Source exactly once per request instead of the daily
    Capture asking for the same facts again. ``raw_root`` is passed in so a test
    can keep every Raw Artifact in a temporary directory.
    """
    raw_dir = raw_root / artifacts.CSI1000_RAW_SUBDIR / target_trade_date
    raw_dir.mkdir(parents=True, exist_ok=True)

    run_capture_stage(
        "csi1000_history",
        csi1000_index_history.RAW_ARTIFACT,
        raw_dir,
        lambda: csi1000_index_history.capture(api, target_trade_date),
    )
    mo_basic_facts = run_capture_stage(
        "mo_option_basic",
        mo_option_basic.RAW_ARTIFACT,
        raw_dir,
        lambda: mo_option_basic.capture(api, target_trade_date),
    )
    run_capture_stage(
        "mo_option_daily",
        mo_option_daily.RAW_ARTIFACT,
        raw_dir,
        lambda: mo_option_daily.capture(api, target_trade_date, mo_basic_facts),
    )
    im_basic_facts = run_capture_stage(
        "im_futures_basic",
        im_futures_basic.RAW_ARTIFACT,
        raw_dir,
        lambda: im_futures_basic.capture(api, target_trade_date),
    )
    run_capture_stage(
        "im_futures_daily",
        im_futures_daily.RAW_ARTIFACT,
        raw_dir,
        lambda: im_futures_daily.capture(api, target_trade_date, im_basic_facts),
    )
    return raw_dir


def orchestrate_csi1000_5d_analysis(
    api: tushare.TushareApi,
    target_trade_date: str,
    raw_root: Path,
    output_root: Path,
) -> Path:
    """Run the whole chain against explicit Raw and output roots."""
    raw_dir = collect_csi1000_5d_analysis(api, target_trade_date, raw_root)
    try:
        snapshot = _preparation.build_snapshot(target_trade_date, raw_dir)
    except _preparation.SnapshotError as exc:
        raise DataServiceError(f"stage=analysis_preparation error={exc}") from exc
    return artifacts.write_analysis_ready_artifact(
        snapshot, SERVICE_ID, target_trade_date, output_root
    )


def run_csi1000_5d_analysis(api: tushare.TushareApi, target_trade_date: str) -> Path:
    """Collect the five Raw Artifacts and publish the canonical artifact.

    Returns the path of the canonical Data Service artifact,
    ``output/csi1000-5d-analysis/<target_trade_date>/snapshot.json``.
    """
    return orchestrate_csi1000_5d_analysis(
        api, target_trade_date, artifacts.RAW_DIR, artifacts.OUTPUT_DIR
    )
