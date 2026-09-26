"""IM Basis Forward Return Association executable Study implementation.

Public Study ID: im-basis-forward-return-association.
Canonical Study authority:
market-research/studies/im_basis_forward_return_association/ARCHITECTURE.md.
"""

from .study import AssociationResult, AssociationStudyError, compute, run_and_retain

__all__ = ["AssociationResult", "AssociationStudyError", "compute", "run_and_retain"]
