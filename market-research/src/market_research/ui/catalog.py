"""Explicit V1 catalog and execution adapters for runnable retained Studies."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from market_snapshot.products import csi1000_im_basis_history as snapshot_product
from market_snapshot.products.csi1000_im_basis_history import CSI1000IMBasisHistoryRequest

from ..studies.im_annualized_basis_baseline import study as baseline
from ..studies.im_basis_forward_return_association import study as association

ExecutionAdapter = Callable[[CSI1000IMBasisHistoryRequest, Path], tuple[Path, ...]]


@dataclass(frozen=True)
class StudyEntry:
    study_id: str
    description: str
    execute: ExecutionAdapter


def _artifacts(output_dir: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in output_dir.iterdir() if path.is_file()))


def _run_baseline(
    request: CSI1000IMBasisHistoryRequest, output_dir: Path
) -> tuple[Path, ...]:
    snapshot = snapshot_product.run_csi1000_im_basis_history(request)
    baseline.run_and_retain(snapshot, output_dir)
    return _artifacts(output_dir)


def _run_association(
    request: CSI1000IMBasisHistoryRequest, output_dir: Path
) -> tuple[Path, ...]:
    snapshot = snapshot_product.run_csi1000_im_basis_history(request)
    association.run_and_retain(snapshot, output_dir)
    return _artifacts(output_dir)


CATALOG: tuple[StudyEntry, ...] = (
    StudyEntry(
        study_id="im-basis-baseline",
        description="Describe historical annualized IM basis distributions and term structure.",
        execute=_run_baseline,
    ),
    StudyEntry(
        study_id="im-basis-forward-return-association",
        description="Assess exploratory association between IM basis and CSI1000 forward returns.",
        execute=_run_association,
    ),
)


def find_study(study_id: str) -> StudyEntry | None:
    for entry in CATALOG:
        if entry.study_id == study_id:
            return entry
    return None
