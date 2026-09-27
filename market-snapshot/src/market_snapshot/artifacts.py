"""Shared local artifact filesystem capability.

This module only holds what the layers genuinely share:

* the Raw artifact root and active Product paths;
* Raw JSON artifact read / write.

It is deliberately thin: it is not a repository, storage or versioning
framework (see ``market-snapshot/ARCHITECTURE.md``).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# One Source row, ready to be serialized to JSON.
RawRecord = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
# Raw Artifact output root: ``data/raw/``.
RAW_DIR = REPO_ROOT / "data" / "raw"
MO_OPTION_CHAIN_RAW_SUBDIR = "mo-option-chain"
MO_OPTION_PREMIUM_RAW_SUBDIR = "mo-option-premium"

def daily_raw_dir(trade_date: str) -> Path:
    """Return the Raw Artifact directory of the daily scenario for one date.

    ``data/raw/<target_trade_date>/`` (products/daily_market_snapshot/data.md 5).
    """
    return RAW_DIR / trade_date


def mo_option_chain_raw_dir(trade_date: str) -> Path:
    """Return this data product's Raw directory for one target date."""
    return RAW_DIR / MO_OPTION_CHAIN_RAW_SUBDIR / trade_date


def mo_option_premium_raw_dir(as_of: str) -> Path:
    """Return MO Premium Plane's goal-scoped Raw directory."""
    return RAW_DIR / MO_OPTION_PREMIUM_RAW_SUBDIR / as_of


def write_raw_artifact(records: Sequence[RawRecord], raw_dir: Path, raw_artifact: str) -> Path:
    """Write one Raw Artifact file and return its path."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{raw_artifact}.json"
    path.write_text(json.dumps(list(records), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_raw_artifact(raw_dir: Path, raw_artifact: str) -> object:
    """Read one Raw Artifact file as decoded JSON."""
    return json.loads((raw_dir / f"{raw_artifact}.json").read_text(encoding="utf-8"))
