"""Dataset-local storage resolution; never creates filesystem state."""

import re
from pathlib import Path


def database_path(dataset: str, storage_root: Path) -> Path:
    """Resolve an owned filename within storage explicitly supplied by the Dataset."""
    if re.fullmatch(r"[a-z0-9_]+", dataset) is None:
        raise ValueError("Dataset identity must match [a-z0-9_]+ for storage")
    return storage_root / f"{dataset}.sqlite3"
