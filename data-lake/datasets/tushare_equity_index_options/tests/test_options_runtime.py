"""Public runtime, strong completeness and owned snapshots using isolated Source facts."""

import sqlite3
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from data_lake import InvalidRequestError, OperationError
from data_lake._domain import ExecutionFailure, Unit
from data_lake._repository import Repository
from data_lake.datasets import tushare_equity_index_options as public
from data_lake.datasets.tushare_equity_index_options import _service, _source
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar._service import _create_service as calendar_create
from data_lake.datasets.tushare_trade_calendar._source import TradeCalSource

DAY = date(2024, 1, 2)


class Frame:
    def __init__(self, records: Any):
        self.records = records

    def to_dict(self, **kwargs: Any) -> Any:
        return self.records


class Executor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.error = False
        self.unpaged = False
        self.catalog = catalog()
        self.daily = [daily(meta) for meta in self.catalog]

    def call(self, endpoint: str, **params: Any) -> Frame:
        self.calls.append((endpoint, params))
        if self.error:
            raise ExecutionFailure("fake provider failure", "source_request")
        if endpoint == "trade_cal":
            first = date.fromisoformat(params["start_date"])
            last = date.fromisoformat(params["end_date"])
            return Frame(
                [
                    {
                        "exchange": params["exchange"],
                        "cal_date": (first + timedelta(days=i)).strftime("%Y%m%d"),
                        "is_open": 1,
                        "pretrade_date": "20231229",
                    }
                    for i in range((last - first).days + 1)
                ]
            )
        if endpoint.endswith("basic"):
            if params.get("fut_type") == "2":
                return Frame([])
            return Frame(
                self.catalog
                if self.unpaged
                else self.catalog[int(params["offset"]) : int(params["offset"]) + 1]
            )
        return Frame(self.daily[int(params.get("offset", 0)) : int(params.get("offset", 0)) + 4000])


def catalog() -> list[dict[str, Any]]:
    result = []
    for month, expiry in [("2401", "20240119"), ("2402", "20240216")]:
        for strike in [3000, 3100]:
            for leg in ["C", "P"]:
                symbol = f"IO{month}-{leg}-{strike}"
                result.append(
                    dict(
                        ts_code=symbol + ".CFX",
                        symbol=symbol,
                        name="option",
                        exchange="CFFEX",
                        opt_code="OP000300.SH",
                        opt_type="指数期权",
                        exercise_type="E",
                        per_unit=100,
                        opt_multiplier=100,
                        quote_unit="point",
                        s_month="20" + month,
                        maturity_date=expiry,
                        exercise_price=strike,
                        call_put=leg,
                        list_date="20231001",
                        delist_date=expiry,
                        last_edate=expiry,
                        last_ddate=None,
                    )
                )
    return result


def daily(meta: dict[str, Any]) -> dict[str, Any]:
    return dict(
        ts_code=meta["ts_code"],
        trade_date="20240102",
        exchange="CFFEX",
        pre_close=1,
        pre_settle=1,
        open=None,
        high=None,
        low=0,
        close=1,
        settle=1,
        vol=0,
        amount=0,
        oi=3,
    )


@pytest.fixture
def setup(tmp_path: Path) -> tuple[Any, Repository, Executor, Any]:
    executor = Executor()
    calendar = calendar_create(
        Repository(tmp_path / "calendar.sqlite3", "tushare_trade_calendar", "tushare"),
        lambda: TradeCalSource(executor),
    )
    repo = Repository(tmp_path / "owned.sqlite3", "tushare_equity_index_options", "tushare")
    service = _service._create_service(repo, calendar, lambda: _source.DailySource(executor))
    request = public.OptionsDailyRange(["IO"], DAY, DAY)
    return service, repo, executor, request


def test_public_runtime_atomic_success_and_cached_read_only(setup: Any) -> None:
    service, repo, executor, request = setup
    with pytest.raises(OperationError, match="Calendar"):
        service.coverage(request)
    assert not repo.path.exists()
    result = service.ensure(request)
    assert (result.requested_units, result.succeeded_units, result.records_written) == (
        1,
        1,
        len(executor.daily),
    )
    assert result.complete
    view = service.export(request)
    assert len(view.records) == len(executor.daily)
    assert view.dataset == "tushare_equity_index_options"
    assert type(view.records[0].trade_date) is date
    before = repo.path.read_bytes()
    calls = len(executor.calls)
    assert service.coverage(request).complete
    assert service.ensure(request).attempted_units == 0
    assert service.export(request).coverage.complete
    assert repo.path.read_bytes() == before and len(executor.calls) == calls
    cached = repo.snapshot((Unit(("IO", DAY)),)).successful[0]
    assert cached.basis is not None
    assert len(cached.records) == len(executor.daily)
    assert "__all__" not in vars(public)
    for name in (
        "OptionsDailyService",
        "OptionsDailyRange",
        "OptionsDailyRow",
        "OptionsDailyExport",
        "create_service",
    ):
        assert hasattr(public, name)


@pytest.mark.parametrize(
    "defect", ["missing", "duplicate", "unexpected", "invalid", "field", "nan", "boolean"]
)
def test_incomplete_unit_is_not_exported(setup: Any, defect: str) -> None:
    service, repo, executor, request = setup
    if defect == "missing":
        executor.daily.pop()
    elif defect == "duplicate":
        executor.daily.append(deepcopy(executor.daily[0]))
    elif defect == "unexpected":
        extra = deepcopy(executor.daily[0])
        extra["ts_code"] = "IO2403-C-3000.CFX"
        executor.daily.append(extra)
    elif defect == "field":
        executor.daily[0].pop("close")
    else:
        executor.daily[0]["close"] = {"invalid": None, "nan": float("nan"), "boolean": True}[defect]
    result = service.ensure(request)
    assert not result.complete and result.failed_units == 1 and result.records_written == 0
    assert result.failures[0].identity == ("IO", DAY)
    assert service.export(request).records == ()
    assert service.coverage(request).failed_units == 1
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0


def test_metadata_exhaustion_and_ignored_offsets(setup: Any) -> None:
    service, _, executor, request = setup
    executor.unpaged = True
    assert service.ensure(request).failed_units == 1
    assert service.export(request).records == ()


def test_complete_calendar_missing_owned_cache_read_only(setup: Any) -> None:
    service, repo, executor, request = setup
    service._calendar.ensure(TradeCalendarRange("CFFEX", DAY, DAY))
    calls = len(executor.calls)
    assert service.coverage(request).missing_units == 1
    assert service.export(request).records == ()
    assert not repo.path.exists() and len(executor.calls) == calls


@pytest.mark.parametrize("values", [[], "IO", ["bad"], [None]])
def test_invalid_request_before_dependency(values: Any) -> None:
    with pytest.raises(InvalidRequestError):
        public.OptionsDailyRange(values, DAY, DAY)


def test_catalog_failure_is_unit_failure_and_retry_succeeds(setup: Any) -> None:
    service, _, executor, request = setup
    service._calendar.ensure(TradeCalendarRange("CFFEX", DAY, DAY))
    executor.error = True
    assert service.ensure(request).failed_units == 1
    executor.error = False
    assert service.ensure(request).complete


def test_proven_empty_universe_retains_product_day(setup: Any) -> None:
    service, repo, executor, request = setup
    executor.catalog = []
    executor.daily = []
    result = service.ensure(request)
    assert result.complete and result.succeeded_units == 1 and result.records_written == 0
    assert service.export(request).records == ()
    assert repo.snapshot((Unit(("IO", DAY)),)).successful[0].basis["catalog"] == []


def test_basis_and_old_metadata_survive_later_catalog_changes(setup: Any) -> None:
    service, _, executor, request = setup
    assert service.ensure(request).complete
    before = service.export(request)
    executor.catalog[0]["name"] = "revised"
    executor.daily = []
    assert service.ensure(request).attempted_units == 0
    assert service.export(request) == before


@pytest.mark.parametrize("field", ["name", "list_date", "delist_date", "symbol"])
def test_invalid_catalog_cannot_prove_success(setup: Any, field: str) -> None:
    service, _, executor, request = setup
    executor.catalog[0][field] = "" if field == "name" else "bad"
    assert service.ensure(request).failed_units == 1


@pytest.mark.parametrize("dimension", ["expiry", "strike", "leg"])
def test_missing_chain_dimension_fails_whole_product(setup: Any, dimension: str) -> None:
    service, _, executor, request = setup
    executor.daily = [
        row
        for row in executor.daily
        if {"expiry": "2402", "strike": "3100", "leg": "-P-"}[dimension] not in row["ts_code"]
    ]
    assert service.ensure(request).failed_units == 1
    assert service.export(request).records == ()


@pytest.mark.parametrize("field", ["vol", "amount"])
def test_positive_trading_forbids_nullable_price(setup: Any, field: str) -> None:
    service, _, executor, request = setup
    executor.daily[0][field] = 1
    assert service.ensure(request).failed_units == 1


def test_export_uses_one_committed_snapshot(setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, executor, request = setup
    assert service.ensure(request).complete
    snapshots = []
    original = repo.snapshot

    def capture(units: Any) -> Any:
        result = original(units)
        snapshots.append(result)
        # Change current storage immediately after the read returns. Projection
        # must retain the coverage and facts from the earlier committed snapshot.
        unit = Unit(("IO", DAY))
        repo.pending(unit)
        repo.failed(unit, ExecutionFailure("concurrent mutation"))
        return result

    monkeypatch.setattr(repo, "snapshot", capture)
    view = service.export(request)
    assert len(snapshots) == 1 and view.coverage.complete
    assert len(view.records) == len(executor.daily)
    assert original((Unit(("IO", DAY)),)).coverage.failed_units == 1


def test_no_trading_days_skips_source_and_storage(
    setup: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, repo, executor, request = setup
    assert service._calendar.ensure(TradeCalendarRange("CFFEX", DAY, DAY)).complete
    original = service._calendar.export

    def closed(request: Any) -> Any:
        view = original(request)
        return replace(view, records=tuple(replace(row, is_open=0) for row in view.records))

    monkeypatch.setattr(service._calendar, "export", closed)
    executor.calls.clear()
    assert service.coverage(request).requested_units == 0
    assert service.ensure(request).complete
    assert service.export(request).records == ()
    assert not executor.calls and not repo.path.exists()


def test_partial_coverage_and_unit_failure_continue(setup: Any) -> None:
    service, _, executor, request = setup
    # Two known open days; Source only supplies the first day's facts.
    request = public.OptionsDailyRange(["IO"], DAY, DAY + timedelta(days=1))
    result = service.ensure(request)
    assert (result.requested_units, result.succeeded_units, result.failed_units) == (2, 1, 1)
    view = service.export(request)
    assert not view.coverage.complete and view.coverage.successful_units == 1
    assert len(view.records) == len(executor.daily)


def test_later_catalog_preserves_old_success_basis(setup: Any) -> None:
    service, repo, executor, request = setup
    assert service.ensure(request).complete
    old = service.export(request)
    old_basis = repo.snapshot((Unit(("IO", DAY)),)).successful[0].basis
    executor.catalog[0]["name"] = "updated metadata"
    for row in executor.daily:
        row["trade_date"] = "20240103"
    next_day = DAY + timedelta(days=1)
    assert service.ensure(public.OptionsDailyRange(["IO"], next_day, next_day)).complete
    assert service.export(request) == old
    assert repo.snapshot((Unit(("IO", DAY)),)).successful[0].basis == old_basis


def test_unrelated_metadata_defect_does_not_fail_selected_product(setup: Any) -> None:
    service, _, executor, request = setup
    bad = deepcopy(executor.catalog[0])
    bad["ts_code"] = bad["ts_code"].replace("IO", "HO", 1)
    bad["symbol"] = bad["symbol"].replace("IO", "HO", 1)
    bad["opt_code"] = "OP000016.SH"
    bad["name"] = ""
    executor.catalog.append(bad)
    assert service.ensure(request).complete


def test_duplicate_catalog_identity_fails(setup: Any) -> None:
    service, _, executor, request = setup
    executor.catalog.append(deepcopy(executor.catalog[0]))
    assert service.ensure(request).failed_units == 1


def test_storage_failure_rolls_back_records_instruments_and_basis(setup: Any) -> None:
    service, repo, _, request = setup
    repo.pending(Unit(("IO", DAY)))
    with sqlite3.connect(repo.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_record BEFORE INSERT ON records "
            "WHEN NEW.facts LIKE '%IO2401-P-3000%' BEGIN "
            "SELECT RAISE(ABORT, 'isolated failure'); END"
        )
    with pytest.raises(OperationError):
        service.ensure(request)
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM instrument").fetchone()[0] == 0
        assert connection.execute("SELECT basis FROM fetch_unit").fetchone()[0] is None
        assert connection.execute("SELECT status FROM fetch_unit").fetchone()[0] != "success"
    assert service.export(request).records == ()


def test_factory_owns_colocated_storage_without_source(monkeypatch: pytest.MonkeyPatch) -> None:
    from data_lake.providers.tushare import _executor

    monkeypatch.setattr(
        _executor, "resolve_credential", lambda: pytest.fail("factory must be lazy")
    )
    dataset_root = Path(__file__).resolve().parents[1]
    expected = dataset_root / "data" / (dataset_root.name + ".sqlite3")
    existed = expected.exists()
    service = public.create_service()
    assert service._repository.path == expected
    assert expected.exists() == existed
