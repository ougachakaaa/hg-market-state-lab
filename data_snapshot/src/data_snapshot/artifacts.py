"""Shared local artifact filesystem capability.

This module only holds what the layers genuinely share:

* the Raw artifact root;
* Raw JSON artifact read / write.

It is deliberately thin: it is not a repository, storage or versioning
framework (see ``data_snapshot/ARCHITECTURE.md``).
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


def check_local_migration() -> None:
    """Refuse split local state before a read, write or Source request."""
    legacy = REPO_ROOT.parent / "market-snapshot"
    if (legacy / "data").exists() or (legacy / ".env").exists():
        raise OSError("Legacy Snapshot state remains; follow LOCAL_MIGRATION.md")


def write_raw_artifact(records: Sequence[RawRecord], raw_dir: Path, raw_artifact: str) -> Path:
    """Write one Raw Artifact file and return its path."""
    check_local_migration()
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{raw_artifact}.json"
    path.write_text(json.dumps(list(records), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_raw_artifact(raw_dir: Path, raw_artifact: str) -> object:
    """Read one Raw Artifact file as decoded JSON."""
    check_local_migration()
    return json.loads((raw_dir / f"{raw_artifact}.json").read_text(encoding="utf-8"))
