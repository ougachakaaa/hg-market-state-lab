"""Compatibility imports for the shared CFFEX basis semantic owner."""

from ...cffex_equity_index_basis.semantics import (
    CALENDAR_DAYS_PER_YEAR,
    SLOT_ORDER,
    assign_contract_slots,
    basis_values,
    contract_month,
    observation_sort_key,
)
from ...cffex_equity_index_basis.semantics import (
    CFFEXBasisError as IMBasisError,
)

__all__ = [
    "IMBasisError",
    "CALENDAR_DAYS_PER_YEAR",
    "SLOT_ORDER",
    "assign_contract_slots",
    "basis_values",
    "contract_month",
    "observation_sort_key",
]
