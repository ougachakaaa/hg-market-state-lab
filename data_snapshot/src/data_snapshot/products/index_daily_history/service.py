"""Public application service for Index Daily History."""

from __future__ import annotations

from datetime import date, timedelta

from ...artifacts import RawRecord
from ...capture import index_daily
from ...sources import tushare
from .models import IndexDailyHistoryRequest, IndexDailyHistoryResult
from .preparation import prepare_history


class IndexDailyHistoryError(Exception):
    """Classified public failure of an Index Daily History request."""


def _validate_request(request: IndexDailyHistoryRequest) -> None:
    code = request.ts_code
    if not isinstance(code, str) or not code or code != code.strip() or any(
        char.isspace() or char == "," for char in code
    ):
        raise IndexDailyHistoryError("ts_code must identify one nonblank index.")
    for field in ("start_trade_date", "end_trade_date"):
        value = getattr(request, field)
        if not isinstance(value, str):
            raise IndexDailyHistoryError(f"{field} must use YYYY-MM-DD.")
        try:
            tushare.to_tushare_date(value)
        except tushare.TushareSourceError as exc:
            raise IndexDailyHistoryError(str(exc)) from exc
    if request.start_trade_date > request.end_trade_date:
        raise IndexDailyHistoryError("start_trade_date must be on or before end_trade_date.")
    count = request.pre_start_observation_count
    if type(count) is not int or count < 0:
        raise IndexDailyHistoryError("pre_start_observation_count must be a nonnegative integer.")


class IndexDailyHistoryService:
    """Capture one index's query-scoped facts and prepare its history in memory."""

    def __init__(self, api: tushare.TushareApi) -> None:
        self._api = api

    def run(self, request: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
        _validate_request(request)
        try:
            sample_facts = index_daily.capture_range(
                self._api, request.start_trade_date, request.end_trade_date, request.ts_code
            )
            if not sample_facts:
                raise IndexDailyHistoryError("no sample observation in the requested interval.")
            pre_start_facts = self._capture_pre_start(request)
            return prepare_history(request, sample_facts, pre_start_facts)
        except IndexDailyHistoryError:
            raise
        except Exception as exc:
            raise IndexDailyHistoryError(str(exc)) from exc

    def _capture_pre_start(self, request: IndexDailyHistoryRequest) -> list[RawRecord]:
        required = request.pre_start_observation_count
        if required == 0:
            return []
        start = date.fromisoformat(request.start_trade_date)
        if start == date.min:
            return []
        end = start - timedelta(days=1)
        facts: list[RawRecord] = []
        while True:
            # Calendar-year segments are contiguous. An empty segment is not
            # evidence that the requested number of actual observations exists.
            beginning = date(end.year, 1, 1)
            facts.extend(
                index_daily.capture_range(
                    self._api, beginning.isoformat(), end.isoformat(), request.ts_code
                )
            )
            if len(facts) >= required or beginning == date.min:
                return facts
            end = beginning - timedelta(days=1)


def run_index_daily_history(request: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
    """Execute one semantic request with Snapshot-owned Source composition."""
    _validate_request(request)
    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
    except Exception as exc:
        raise IndexDailyHistoryError(str(exc)) from exc
    return IndexDailyHistoryService(api).run(request)
