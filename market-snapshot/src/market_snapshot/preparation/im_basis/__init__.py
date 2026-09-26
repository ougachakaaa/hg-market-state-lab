"""Canonical deterministic IM term-structure and basis preparation."""

from .semantics import (
    SLOT_ORDER,
    IMBasisError,
    assign_contract_slots,
    basis_values,
    observation_sort_key,
)

__all__ = [
    "IMBasisError",
    "SLOT_ORDER",
    "assign_contract_slots",
    "basis_values",
    "observation_sort_key",
]
