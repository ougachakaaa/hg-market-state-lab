"""Public boundary of CFFEX Equity Index Futures Basis History."""

from .models import (
    CFFEXEquityIndexBasisHistoryRequest,
    CFFEXEquityIndexBasisHistoryResult,
    CFFEXEquityIndexBasisObservation,
)
from .service import (
    CFFEXEquityIndexBasisHistoryError,
    run_cffex_equity_index_basis_history,
)

__all__ = [
    "CFFEXEquityIndexBasisHistoryRequest",
    "CFFEXEquityIndexBasisHistoryResult",
    "CFFEXEquityIndexBasisObservation",
    "CFFEXEquityIndexBasisHistoryError",
    "run_cffex_equity_index_basis_history",
]
