"""Dataset-local storage resolution; never creates filesystem state."""

import re
from pathlib import Path


def database_path(dataset: str, storage_root: Path | None = None) -> Path:
    """Use the canonical Dataset ID as the readable owned SQLite filename."""
    if re.fullmatch(r"[a-z0-9_]+", dataset) is None:
        raise ValueError("Dataset identity must match [a-z0-9_]+ for storage")
    root = (
        storage_root if storage_root is not None else Path(__file__).resolve().parents[2] / "data"
    )
    return root / f"{dataset}.sqlite3"
