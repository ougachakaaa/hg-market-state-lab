"""Data Service ``csi1000-5d-analysis``: orchestration of the whole chain.

Authority: ``guides/data-services.md`` (Data Service catalogue, CLI contract,
canonical output) over ``guides/csi1000-5d-analysis-data.md`` (Raw Artifacts) and
``guides/csi1000-5d-analysis-snapshot.md`` (Analysis Preparation Definition).

The Data Service owns orchestration only: it runs the required Source Captures in
order, writes their Raw Artifacts, calls the deterministic Analysis Preparation
and publishes the canonical analysis-ready artifact. It redefines neither Source
Capture semantics nor Preparation formulas.

Canonical output:

    output/csi1000-5d-analysis/<target_trade_date>/snapshot.json
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

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


@dataclass(frozen=True)
class Stage:
    """One collection stage: the name it is reported under and its Raw Artifact.

    ``raw_artifact`` is the Raw Artifact name, which is not always the stage name:
    the CSI1000 history stage writes the ``index_daily_history`` artifact of the
    ``index_daily`` Source Capture (see ``guides/csi1000-5d-analysis-data.md`` 8).
    """

    name: str
    raw_artifact: str
    collect: Callable[[], list[artifacts.RawRecord]]


def stage_query(api: tushare.TushareApi, endpoint: str, **params: str) -> Any:
    """Bind one Source endpoint call so a Capture can query it.

    Tushare resolves endpoints dynamically, so the endpoint is looked up on the
    client instead of being named as a method of the protocol. ``params`` is the
    shared part of the request; a Capture that supplies its own value for one
    of those keys (the MO and IM captures pass their product limit
    themselves) keeps the last word.
    """
    return lambda **kwargs: getattr(api, endpoint)(**(params | kwargs))


def collect_csi1000_5d_analysis(
    api: tushare.TushareApi, target_trade_date: str, raw_root: Path
) -> Path:
    """Run the five CSI1000 analysis collection stages for one target trade date.

    Authority order (``guides/data-services.md`` section 5):

        CSI1000 history -> MO option basic -> MO option daily ->
        IM futures basic -> IM futures daily

    Each stage writes its own Raw Artifact, named after its Dataset. A stage that
    raises a collection failure is reported as the failed stage and stops the
    chain, so no later Dataset is collected and no Analysis Preparation runs.
    ``raw_root`` is passed in so a test can keep every Raw Artifact in a
    temporary directory.
    """
    # The two contract universes are Source facts both the basic and the daily
    # Dataset of their product need, so they are read once here instead of being
    # requested twice. Both belong to the first stages of the chain, so a failure
    # is still reported before any Dataset is written.
    basic_options = mo_option_basic.query_opt_basic(api, mo_option_basic.EXCHANGE)
    basic_futures = im_futures_basic.query_fut_basic(
        api,
        exchange=im_futures_basic.EXCHANGE,
        fut_type=im_futures_basic.FUTURES_TYPE_ORDINARY,
        fut_code=im_futures_basic.PRODUCT,
    )

    # The stages of Guide section 5, in order. They run one at a time: a failing
    # stage must stop the chain before any later Dataset is collected.
    stages: tuple[Stage, ...] = (
        Stage(
            "csi1000_history",
            csi1000_index_history.DATASET,
            lambda: csi1000_index_history.collect_index_daily_history(
                target_trade_date, stage_query(api, "index_daily")
            ),
        ),
        Stage(
            "mo_option_basic",
            mo_option_basic.DATASET,
            lambda: mo_option_basic.collect_mo_option_basic(
                target_trade_date,
                stage_query(api, "opt_basic", exchange=mo_option_basic.EXCHANGE),
            ),
        ),
        Stage(
            "mo_option_daily",
            mo_option_daily.DATASET,
            lambda: mo_option_daily.collect_mo_option_daily(
                target_trade_date,
                basic_options,
                stage_query(api, "opt_daily", exchange=mo_option_basic.EXCHANGE),
            ),
        ),
        Stage(
            "im_futures_basic",
            im_futures_basic.DATASET,
            lambda: im_futures_basic.collect_im_futures_basic(
                target_trade_date,
                stage_query(
                    api,
                    "fut_basic",
                    exchange=im_futures_basic.EXCHANGE,
                    fut_type=im_futures_basic.FUTURES_TYPE_ORDINARY,
                    fut_code=im_futures_basic.PRODUCT,
                ),
            ),
        ),
        Stage(
            "im_futures_daily",
            im_futures_daily.DATASET,
            lambda: im_futures_daily.collect_im_futures_daily(
                target_trade_date,
                basic_futures,
                stage_query(api, "fut_daily"),
            ),
        ),
    )

    dataset_dir = raw_root / artifacts.CSI1000_RAW_SUBDIR / target_trade_date
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for stage in stages:
        try:
            records = stage.collect()
        except capture_common.CAPTURE_FAILURE_TYPES as exc:
            raise DataServiceError(f"stage={stage.name} error={exc}") from exc
        artifacts.write_raw_artifact(records, dataset_dir, stage.raw_artifact)
    return dataset_dir


def orchestrate_csi1000_5d_analysis(
    api: tushare.TushareApi,
    target_trade_date: str,
    raw_root: Path,
    output_root: Path,
) -> Path:
    """Run the whole chain against explicit Raw and output roots."""
    dataset_dir = collect_csi1000_5d_analysis(api, target_trade_date, raw_root)
    try:
        snapshot = _preparation.build_snapshot(target_trade_date, dataset_dir)
    except _preparation.SnapshotError as exc:
        raise DataServiceError(f"stage=snapshot_assembly error={exc}") from exc
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
