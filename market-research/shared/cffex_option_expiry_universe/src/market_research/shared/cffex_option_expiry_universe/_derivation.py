"""Observed-window expiry extraction and complete result invariants."""

from data_lake.datasets.tushare_equity_index_options import OptionsDailyExport

from ._models import ExpiryUniverseRequest, ExpiryUniverseResult
from ._upstream import options_provenance


def derive(request: ExpiryUniverseRequest, view: OptionsDailyExport) -> ExpiryUniverseResult:
    return ExpiryUniverseResult(
        request.product_code,
        request.expiry_start_date,
        request.expiry_end_date,
        tuple(
            sorted(
                {
                    row.expiry
                    for row in view.records
                    if request.expiry_start_date <= row.expiry <= request.expiry_end_date
                }
            )
        ),
        True,
        options_provenance(view),
    )
