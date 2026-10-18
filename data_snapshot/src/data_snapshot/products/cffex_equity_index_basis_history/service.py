"""Public application composition for CFFEX equity-index basis history."""

from __future__ import annotations

from datetime import date

from ...capture import im_futures_basic, im_futures_daily, index_daily
from ...capture.common import CollectionError
from ...cffex_equity_index_basis.semantics import FAMILY_FACTS
from ...sources import tushare
from .models import CFFEXEquityIndexBasisHistoryRequest, CFFEXEquityIndexBasisHistoryResult
from .preparation import IncompletePanelError, NoObservationsError, prepare_history


class CFFEXEquityIndexBasisHistoryError(Exception):
    """Classified product failure with a stable public reason."""

    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        super().__init__(message)


def _validate(request: CFFEXEquityIndexBasisHistoryRequest) -> None:
    if not isinstance(request.futures_family, str) or request.futures_family not in FAMILY_FACTS:
        raise CFFEXEquityIndexBasisHistoryError("invalid_request", "unsupported futures family.")
    for field in ("start_trade_date", "end_trade_date"):
        value = getattr(request, field)
        try:
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError as exc:
            raise CFFEXEquityIndexBasisHistoryError(
                "invalid_request", f"{field} must use a valid YYYY-MM-DD date."
            ) from exc
    if request.start_trade_date > request.end_trade_date:
        raise CFFEXEquityIndexBasisHistoryError(
            "invalid_request", "start_trade_date must not exceed end_trade_date."
        )


class CFFEXEquityIndexBasisHistoryService:
    """Injectable Source composition for one public semantic request."""

    def __init__(self, api: tushare.TushareApi) -> None:
        self._api = api

    def run(
        self, request: CFFEXEquityIndexBasisHistoryRequest
    ) -> CFFEXEquityIndexBasisHistoryResult:
        _validate(request)
        family = request.futures_family
        underlying_code, listing_date = FAMILY_FACTS[family]
        effective_start = max(request.start_trade_date, listing_date)
        if effective_start > request.end_trade_date:
            raise CFFEXEquityIndexBasisHistoryError(
                "no_observations", "request ends before family listing."
            )
        try:
            index_facts = index_daily.capture_range(
                self._api, effective_start, request.end_trade_date, underlying_code
            )
            if not index_facts:
                raise NoObservationsError("effective interval has no underlying observation dates.")
            basic_facts = im_futures_basic.capture(self._api, request.end_trade_date, family)
            daily_facts = im_futures_daily.capture_range(
                self._api, effective_start, request.end_trade_date, basic_facts, family
            )
            return prepare_history(
                family,
                request.start_trade_date,
                request.end_trade_date,
                index_facts,
                basic_facts,
                daily_facts,
            )
        except NoObservationsError as exc:
            raise CFFEXEquityIndexBasisHistoryError("no_observations", str(exc)) from exc
        except (IncompletePanelError, CollectionError) as exc:
            raise CFFEXEquityIndexBasisHistoryError("incomplete_panel", str(exc)) from exc
        except tushare.TushareSourceError as exc:
            raise CFFEXEquityIndexBasisHistoryError("source_failure", str(exc)) from exc


def run_cffex_equity_index_basis_history(
    request: CFFEXEquityIndexBasisHistoryRequest,
) -> CFFEXEquityIndexBasisHistoryResult:
    """Execute the product without exposing credentials or Source clients to Research."""
    _validate(request)
    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
    except Exception as exc:
        raise CFFEXEquityIndexBasisHistoryError("source_failure", str(exc)) from exc
    return CFFEXEquityIndexBasisHistoryService(api).run(request)
