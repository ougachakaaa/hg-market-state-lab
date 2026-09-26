"""Public application service for CSI1000 IM Basis History."""

from __future__ import annotations

from ...capture import im_futures_basic, im_futures_daily, index_daily
from ...capture.common import CAPTURE_FAILURE_TYPES
from ...sources import tushare
from .models import CSI1000IMBasisHistoryRequest, CSI1000IMBasisHistoryResult
from .preparation import UNDERLYING_TS_CODE, IMBasisHistoryError, prepare_history

APPLICATION_FAILURES: tuple[type[Exception], ...] = (
    *CAPTURE_FAILURE_TYPES,
    IMBasisHistoryError,
)


class CSI1000IMBasisHistoryError(Exception):
    """Classified public application failure for the historical product."""


class CSI1000IMBasisHistoryService:
    """Capture and prepare one explicit historical request in memory."""

    def __init__(self, api: tushare.TushareApi) -> None:
        self._api = api

    def run(self, request: CSI1000IMBasisHistoryRequest) -> CSI1000IMBasisHistoryResult:
        _validate_request(request)
        try:
            index_facts = index_daily.capture_range(
                self._api,
                request.start_trade_date,
                request.end_trade_date,
                UNDERLYING_TS_CODE,
            )
            basic_facts = im_futures_basic.capture(self._api, request.end_trade_date)
            daily_facts = im_futures_daily.capture_range(
                self._api,
                request.start_trade_date,
                request.end_trade_date,
                basic_facts,
            )
            return prepare_history(
                request.start_trade_date,
                request.end_trade_date,
                index_facts,
                basic_facts,
                daily_facts,
            )
        except APPLICATION_FAILURES as exc:
            raise CSI1000IMBasisHistoryError(str(exc)) from exc


def _validate_request(request: CSI1000IMBasisHistoryRequest) -> None:
    try:
        tushare.to_tushare_date(request.start_trade_date)
        tushare.to_tushare_date(request.end_trade_date)
    except tushare.TushareSourceError as exc:
        raise CSI1000IMBasisHistoryError(str(exc)) from exc
    if request.start_trade_date > request.end_trade_date:
        raise CSI1000IMBasisHistoryError(
            "start_trade_date must be on or before end_trade_date."
        )


def run_csi1000_im_basis_history(
    request: CSI1000IMBasisHistoryRequest,
) -> CSI1000IMBasisHistoryResult:
    """Execute one request using Snapshot-owned production composition."""
    _validate_request(request)
    try:
        token = tushare.get_tushare_token()
        api = tushare.create_tushare_api(token)
    except Exception as exc:
        raise CSI1000IMBasisHistoryError(str(exc)) from exc
    return CSI1000IMBasisHistoryService(api).run(request)
