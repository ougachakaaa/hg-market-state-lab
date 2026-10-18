"""Concrete date-resolution orchestration and durable complete publication."""

from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_trade_calendar as calendar

from .. import ObservationInvalidRequestError, ObservationOperationError
from .._sqlite import owned_path
from . import _persistence
from ._date_resolution import calendar_provenance, calendar_window, candidate_day, ideal_date
from ._derivation import derive, validate
from ._models import CalendarProvenance, ExpiryDteChainArtifact, ExpiryDteChainRequest


class ExpiryDteChainService:
    def __init__(
        self,
        *,
        _path: Path,
        _options_factory: Callable[[], options.OptionsDailyService],
        _calendar_factory: Callable[[], calendar.TradeCalendarService],
    ):
        """Private test composition; ordinary consumers use create_service()."""
        self._path = _path
        self._options_factory = _options_factory
        self._calendar_factory = _calendar_factory

    def ensure(self, request: ExpiryDteChainRequest) -> ExpiryDteChainArtifact:
        if not isinstance(request, ExpiryDteChainRequest):
            raise ObservationInvalidRequestError("Expected ExpiryDteChainRequest")
        request.__post_init__()
        try:
            retained = _persistence.load(self._path, request)
            if retained is not None:
                validate(retained, request)
                return retained
            ideal = ideal_date(request.expiry_date, request.target_dte)
            calendar_service = self._calendar_factory()
            options_service = None
            contexts: list[CalendarProvenance] = []
            end = ideal
            while True:
                # Bounded proof chunks, without a historical cutoff or fallback limit.
                start = date.fromordinal(max(date.min.toordinal(), end.toordinal() - 30))
                view = calendar_window(calendar_service, start, end)
                contexts.append(calendar_provenance(view))
                for row in reversed(view.records):
                    if row.is_open != 1:
                        continue
                    if options_service is None:
                        options_service = self._options_factory()
                    facts = candidate_day(options_service, request.product_code, row.cal_date)
                    if not any(fact.expiry == request.expiry_date for fact in facts.records):
                        continue
                    artifact = derive(request, ideal, row.cal_date, facts, tuple(contexts))
                    validate(artifact, request)
                    retained = _persistence.publish(self._path, request, artifact)
                    validate(retained, request)
                    return retained
                if start == date.min:
                    raise ValueError("No representable earlier Calendar date")
                end = start - timedelta(days=1)
        except Exception as error:
            raise ObservationOperationError(f"ExpiryDteChain ensure failed: {error}") from error


def create_service() -> ExpiryDteChainService:
    try:
        return ExpiryDteChainService(
            _path=owned_path(
                "market_research/observations/cffex_option_expiry_dte_chain",
                "cffex_option_expiry_dte_chain.sqlite3",
            ),
            _options_factory=options.create_service,
            _calendar_factory=calendar.create_service,
        )
    except Exception as error:
        raise ObservationOperationError(
            f"ExpiryDteChainService construction failed: {error}"
        ) from error
