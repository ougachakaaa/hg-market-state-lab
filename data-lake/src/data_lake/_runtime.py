"""Dataset-local storage resolution; never creates filesystem state."""

import hashlib
from pathlib import Path


def database_path(dataset: str, storage_root: Path | None = None) -> Path:
    if not dataset:
        raise ValueError("Dataset identity must not be empty")
    root = (
        storage_root if storage_root is not None else Path(__file__).resolve().parents[2] / "data"
    )
    return root / (hashlib.sha256(dataset.encode("utf-8")).hexdigest() + ".sqlite3")
