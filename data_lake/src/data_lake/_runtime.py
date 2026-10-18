"""Dataset-local storage resolution; never creates filesystem state."""

import re
from pathlib import Path

from .results import OperationError


def database_path(dataset: str, storage_root: Path) -> Path:
    """Resolve an owned filename within storage explicitly supplied by the Dataset."""
    if re.fullmatch(r"[a-z0-9_]+", dataset) is None:
        raise ValueError("Dataset identity must match [a-z0-9_]+ for storage")
    for module in storage_root.parents:
        if module.name == "data_lake" and (module.parent / "pyproject.toml").is_file():
            legacy = module.parent / "data-lake" / storage_root.relative_to(module)
            if legacy.exists():
                raise OperationError("Legacy Dataset state remains; follow LOCAL_MIGRATION.md")
            break
    return storage_root / f"{dataset}.sqlite3"
