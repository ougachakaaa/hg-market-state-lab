"""Canonical Research run placement and transactional publication."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from market_snapshot.products.csi1000_im_basis_history import CSI1000IMBasisHistoryRequest

from .catalog import StudyEntry


class ResearchOutputError(OSError):
    """A canonical Research run could not be safely written or replaced."""


def canonical_run_directory(
    output_root: Path, study_id: str, start_trade_date: str, end_trade_date: str
) -> Path:
    return (output_root / study_id / f"{start_trade_date}__{end_trade_date}").resolve(
        strict=False
    )


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _validate_existing_run(path: Path) -> None:
    if _present(path) and (path.is_symlink() or not path.is_dir()):
        raise ResearchOutputError(f"canonical run path is not a directory: {path}.")


def execute_run(
    entry: StudyEntry,
    request: CSI1000IMBasisHistoryRequest,
    run_directory: Path,
    *,
    overwrite: bool,
) -> tuple[Path, ...]:
    """Run in staging, then publish the complete directory as one unit."""
    _validate_existing_run(run_directory)
    if _present(run_directory) and not overwrite:
        raise ResearchOutputError(
            f"run directory already exists: {run_directory}; use --overwrite to replace it."
        )

    staging: Path | None = None
    backup: Path | None = None
    try:
        run_directory.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{run_directory.name}.staging-", dir=run_directory.parent
            )
        )
        artifacts = entry.execute(request, staging)

        _validate_existing_run(run_directory)
        if _present(run_directory):
            if not overwrite:
                raise ResearchOutputError(
                    f"run directory appeared during execution: {run_directory}."
                )
            backup = Path(
                tempfile.mkdtemp(
                    prefix=f".{run_directory.name}.backup-", dir=run_directory.parent
                )
            )
            backup.rmdir()
            run_directory.rename(backup)
        staging.rename(run_directory)
        staging = None

        if backup is not None:
            shutil.rmtree(backup)
            backup = None
        return tuple(run_directory / artifact.name for artifact in artifacts)
    except ResearchOutputError:
        raise
    except OSError as exc:
        if backup is not None and _present(backup) and not _present(run_directory):
            try:
                backup.rename(run_directory)
                backup = None
            except OSError as restore_exc:
                raise ResearchOutputError(
                    f"output publication failed and the prior run could not be restored: "
                    f"{restore_exc}"
                ) from exc
        raise ResearchOutputError(str(exc)) from exc
    finally:
        if staging is not None and _present(staging):
            shutil.rmtree(staging, ignore_errors=True)
