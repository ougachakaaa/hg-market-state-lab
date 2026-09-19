"""Shared local artifact filesystem capability.

This module only holds what the layers genuinely share:

* the canonical artifact roots;
* Raw / Analysis-ready artifact path construction;
* JSON artifact read / write.

It is deliberately thin: it is not a repository, storage or versioning
framework (see ``ARCHITECTURE.md`` 9 and 10).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# One Source row or one Analysis-ready row, ready to be serialized to JSON.
RawRecord = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
# Raw Artifact output root: ``data/raw/`` (ARCHITECTURE.md 9).
RAW_DIR = REPO_ROOT / "data" / "raw"
# Analysis-ready output root of the first-version daily-market-snapshot
# Definition (``data/snapshots/YYYY-MM-DD/``). A Data Service writes its
# canonical user-facing output under ``OUTPUT_DIR`` instead.
SNAPSHOTS_DIR = REPO_ROOT / "data" / "snapshots"
# Data Service canonical user-facing output root of guides/data-services.md
# section 6: ``output/<service_id>/<target_trade_date>/``.
OUTPUT_DIR = REPO_ROOT / "output"

# Data Service id of the CSI1000 analysis scenario, which is also its goal
# scoped Raw sub directory (guides/data-services.md section 2).
CSI1000_RAW_SUBDIR = "csi1000-5d-analysis"

# File name of a Data Service analysis-ready artifact. The canonical location is
# ``output/<service_id>/<target_trade_date>/snapshot.json``
# (guides/data-services.md 6); the file name is the artifact's, not the layer's.
ANALYSIS_READY_FILENAME = "snapshot.json"


def daily_raw_dir(trade_date: str) -> Path:
    """Return the Raw Artifact directory of the daily scenario for one date.

    ``data/raw/<target_trade_date>/`` (guides/daily-market-snapshot.md 5).
    """
    return RAW_DIR / trade_date


def csi1000_raw_dir(trade_date: str) -> Path:
    """Return the goal-scoped Raw Artifact directory of one target trade date.

    ``data/raw/csi1000-5d-analysis/<target_trade_date>/``
    (guides/csi1000-5d-analysis-data.md 7).
    """
    return RAW_DIR / CSI1000_RAW_SUBDIR / trade_date


def write_raw_artifact(records: Sequence[RawRecord], raw_dir: Path, raw_artifact: str) -> Path:
    """Write one Raw Artifact file and return its path."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{raw_artifact}.json"
    path.write_text(json.dumps(list(records), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_raw_artifact(raw_dir: Path, raw_artifact: str) -> object:
    """Read one Raw Artifact file as decoded JSON."""
    return json.loads((raw_dir / f"{raw_artifact}.json").read_text(encoding="utf-8"))


def output_dir(output_root: Path, service_id: str, target_trade_date: str) -> Path:
    """Return the canonical user-facing output directory of one service request."""
    return output_root / service_id / target_trade_date


def write_analysis_ready_artifact(
    payload: RawRecord, service_id: str, target_trade_date: str, output_root: Path
) -> Path:
    """Write the service artifact ``snapshot.json`` and return its path.

    The canonical Data Service location is
    ``output/<service_id>/<target_trade_date>/snapshot.json``
    (guides/data-services.md 6).
    """
    directory = output_dir(output_root, service_id, target_trade_date)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ANALYSIS_READY_FILENAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
