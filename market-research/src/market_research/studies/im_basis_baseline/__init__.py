"""IM Annualized Basis Baseline executable Study implementation.

Public Study ID: im-basis-baseline.
Canonical Study authority: market-research/studies/im_basis_baseline/ARCHITECTURE.md.
"""

from .study import BaselineResult, BaselineStudyError, compute, run_and_retain

__all__ = ["BaselineResult", "BaselineStudyError", "compute", "run_and_retain"]
