"""Read-only admission policy, separate from final acquisition and payload validation."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from data_lake import CoverageResult, OperationError
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord
from futures_basis_observation_fixtures import REQUEST, Services, proof
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    InputPreparationError,
    preflight_inputs,
    prepare_inputs,
    validate_online_request,
)

TODAY = date(2026, 11, 10)
NOW = datetime(2026, 11, 10, 14, tzinfo=UTC)


class Readers:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.missing = set()
        self.calendar_missing = set()
        self.errors = {}

    def export(self, request):
        name = request.exchange
        self.calls.append((name, "export", request.start_date, request.end_date))
        if name in self.errors:
            raise self.errors[name]
        days = tuple(
            request.start_date + timedelta(days=i)
            for i in range((request.end_date - request.start_date).days + 1)
        )
        missing = name in self.calendar_missing
        return TradeCalendarExport(
            "tushare_trade_calendar",
            "calendar",
            1,
            SimpleNamespace(exchange=name),
            SimpleNamespace(start_date=request.start_date, end_date=request.end_date),
            proof(len(days), len(days) if missing else 0),
            ()
            if missing
            else tuple(TradeCalendarRecord(name, d, int(not self.closed), None) for d in days),
        )

    def coverage(self, request):
        name = "futures" if hasattr(request, "product_codes") else "index"
        self.calls.append((name, "coverage", request.start_date, request.end_date))
        if name in self.errors:
            raise self.errors[name]
        n = 0 if self.closed else (request.end_date - request.start_date).days + 1
        missing = name in self.missing or (name, request.start_date) in self.missing
        return proof(n, n if missing else 0)

    def ensure(self, request):
        raise AssertionError("Preflight acquired facts")


def assess(readers, start=TODAY, end=TODAY):
    return preflight_inputs(
        FuturesBasisRequest("IM", start, end),
        calendar_service=readers,
        futures_service=readers,
        index_service=readers,
        clock=lambda: NOW,
    )


def test_today_complete_reuses_single_day_and_checks_no_market_export():
    readers = Readers()
    result = assess(readers)
    assert (result.submission, result.today_gate) == ("allowed", "ready")
    assert len(readers.calls) == 4 and len(result.dependencies) == 8
    assert all(
        c[1] == ("export" if c[0] in ("CFFEX", "SSE") else "coverage") for c in readers.calls
    )
    assert result.checked_at == "2026-11-10T14:00:00Z"


@pytest.mark.parametrize("name", ["futures", "index"])
def test_today_missing_blocks_but_same_historical_gap_is_confirmable(name):
    readers = Readers()
    readers.missing.add(name)
    assert assess(readers).submission == "blocked"
    historical = assess(readers, TODAY - timedelta(days=1), TODAY - timedelta(days=1))
    assert (historical.submission, historical.today_gate) == ("confirm_required", "not_applicable")


def test_history_gap_does_not_mislabel_complete_today():
    readers = Readers()
    readers.missing.add(("futures", TODAY - timedelta(days=2)))
    result = assess(readers, TODAY - timedelta(days=2))
    assert (result.submission, result.today_gate) == ("confirm_required", "ready")
    assert len(readers.calls) == 8


def test_calendar_gap_preserves_unknown_and_skips_dependent_coverage():
    readers = Readers()
    readers.calendar_missing.add("CFFEX")
    result = assess(readers)
    futures = next(item for item in result.dependencies if item.dependency == "futures")
    assert futures.state == "unknown" and futures.coverage is None
    assert not any(c[0] == "futures" for c in readers.calls)
    assert (result.submission, result.today_gate) == ("blocked", "unknown")
    assert (
        assess(readers, TODAY - timedelta(days=1), TODAY - timedelta(days=1)).submission
        == "confirm_required"
    )


def test_closed_sessions_are_ready_with_zero_market_targets():
    readers = Readers()
    readers.closed = True
    result = assess(readers)
    assert result.submission == "allowed"
    assert all(
        item.coverage.requested_units == 0
        for item in result.dependencies
        if item.dependency in ("futures", "index")
    )


@pytest.mark.parametrize(
    "error,state",
    [
        (OperationError("/private token"), "operation_error"),
        (ValueError("malformed"), "contract_error"),
    ],
)
def test_classified_errors_block_without_exposing_exception(error, state, caplog):
    readers = Readers()
    readers.errors["CFFEX"] = error
    with caplog.at_level("INFO"):
        result = assess(readers)
    assert result.submission == "blocked" and result.dependencies[0].state == state
    assert "/private" not in repr(result) and "malformed" not in repr(result)
    record = caplog.records[0]
    assert record.correlation_id and record.exception_type == type(error).__name__
    assert record.operation == "export" and record.duration_seconds >= 0


def test_unexpected_defects_propagate():
    readers = Readers()
    readers.errors["futures"] = RuntimeError("bug")
    with pytest.raises(RuntimeError):
        assess(readers)


@pytest.mark.parametrize(
    "bad",
    [
        CoverageResult(1, True, 0, 0, 0, True),
        CoverageResult(1, 0, 1, 0, 0, True),
        CoverageResult(3, 3, 0, 0, 0, True),
    ],
)
def test_malformed_market_coverage_is_contract_error(bad):
    readers = Readers()
    readers.coverage = Mock(return_value=bad)
    assert assess(readers).dependencies[2].state == "contract_error"


def test_l1_runs_before_factories_and_uses_shanghai_date(monkeypatch):
    module = __import__(preflight_inputs.__module__, fromlist=["create_calendar_service"])
    factory = Mock(side_effect=AssertionError("factory called"))
    monkeypatch.setattr(module, "create_calendar_service", factory)
    for request in (
        FuturesBasisRequest("BAD", TODAY, TODAY),
        FuturesBasisRequest("IM", TODAY, TODAY + timedelta(days=1)),
        FuturesBasisRequest("IM", TODAY - timedelta(days=1096), TODAY),
    ):
        with pytest.raises(ValueError):
            preflight_inputs(request, clock=lambda: NOW)
    factory.assert_not_called()
    validate_online_request(
        FuturesBasisRequest("IM", TODAY - timedelta(days=1095), TODAY), today=TODAY
    )
    readers = Readers()
    instant = datetime(2026, 11, 9, 16, tzinfo=UTC)
    result = preflight_inputs(
        FuturesBasisRequest("IM", TODAY, TODAY),
        calendar_service=readers,
        futures_service=readers,
        index_service=readers,
        clock=lambda: instant,
    )
    assert result.market_date == TODAY


def test_complete_preflight_does_not_bypass_final_export_validation():
    services = Services()
    readers = Readers()
    result = assess(readers, REQUEST.start_date, REQUEST.end_date)
    assert result.submission == "allowed"
    services.futures = replace(services.futures, view="wrong")
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(
            REQUEST, calendar_service=services, futures_service=services, index_service=services
        )
    assert exc.value.category == "invalid_public_input"
    assert not any(operation == "ensure" for _, operation in services.calls)


def test_cold_cache_without_credentials_creates_no_databases(tmp_path, monkeypatch):
    import importlib

    # Test-only storage isolation; the consumer itself calls public APIs only.
    for name in ("tushare_trade_calendar", "tushare_equity_index_futures", "tushare_index_daily"):
        composition = importlib.import_module(f"data_lake.datasets.{name}._composition")
        service_module = importlib.import_module(f"data_lake.datasets.{name}._service")
        monkeypatch.setattr(
            service_module, "prepare_source", Mock(side_effect=AssertionError("Source initialized"))
        )
        monkeypatch.setattr(
            composition, "database_path", lambda dataset, root: tmp_path / dataset / "cache.sqlite3"
        )
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    module = importlib.import_module(preflight_inputs.__module__)
    original = module.create_calendar_service
    calendar = original()
    result = preflight_inputs(
        FuturesBasisRequest("IM", TODAY, TODAY), calendar_service=calendar, clock=lambda: NOW
    )
    assert result.submission == "blocked" and result.today_gate == "unknown"
    assert not list(tmp_path.iterdir())
