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


@pytest.mark.parametrize("missing", [None, float("nan"), ""])
def test_listing_day_pre_close_is_absent_source_fact(setup: Any, missing: object) -> None:
    service, _, executor, request = setup
    executor.catalog[0]["list_date"] = "20240102"
    executor.daily[0]["pre_close"] = missing
    # Legitimate first-day trading with no prior close is independent of volume.
    executor.daily[0].update(vol=10, amount=20, open=1, high=2, low=1)
    assert service.ensure(request).complete
    view = service.export(request)
    assert view.export_schema_version == 2
    assert view.records[0].pre_close is None
    assert view.records[0].pre_settle == 1
    assert service.coverage(request).complete


@pytest.mark.parametrize("defect", ["later_day", "missing_field", "infinity", "boolean"])
def test_listing_exception_does_not_hide_bad_source_facts(setup: Any, defect: str) -> None:
    service, _, executor, request = setup
    executor.catalog[0]["list_date"] = "20240102"
    executor.daily[0]["pre_close"] = None
    if defect == "later_day":
        executor.catalog[0]["list_date"] = "20240101"
    elif defect == "missing_field":
        executor.daily[0].pop("pre_close")
    elif defect == "infinity":
        executor.daily[0]["pre_close"] = float("inf")
    else:
        executor.daily[0]["pre_close"] = True
    result = service.ensure(request)
    assert not result.complete and result.failed_units == 1
    assert service.export(request).records == ()
    if defect != "missing_field":
        assert "field=pre_close" in result.failures[0].reason
        assert "contract=" in result.failures[0].reason
        assert "date=2024-01-02" in result.failures[0].reason


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
def test_future_window_rejected_before_dependency_or_source(setup: Any, operation: str) -> None:
    service, repo, executor, request = setup
    object.__setattr__(request, "end_date", date(9999, 12, 31))
    with pytest.raises(InvalidRequestError, match="today"):
        getattr(service, operation)(request)
    assert not executor.calls and not repo.path.exists()
    with pytest.raises(InvalidRequestError, match="today"):
        public.OptionsDailyRange(["IO"], DAY, date(9999, 12, 31))


@pytest.mark.parametrize("defect", ["value", "identity"])
def test_range_fetch_partitions_days_and_keeps_failure_local(setup: Any, defect: str) -> None:
    service, repo, executor, _ = setup
    original = deepcopy(executor.daily)
    executor.daily = []
    for index in range(3):
        for raw in original:
            item = dict(raw, trade_date=(DAY + timedelta(days=index)).strftime("%Y%m%d"))
            if index == 1:
                if defect == "value":
                    item["close"] = None
                elif raw is original[0]:
                    item["ts_code"] = "malformed"
            executor.daily.append(item)
    request = public.OptionsDailyRange(["IO"], DAY, DAY + timedelta(days=2))
    result = service.ensure(request)
    assert (result.attempted_units, result.succeeded_units, result.failed_units) == (3, 2, 1)
    assert result.failures[0].identity == ("IO", DAY + timedelta(days=1))
    view = service.export(request)
    assert {row.trade_date for row in view.records} == {DAY, DAY + timedelta(days=2)}
    calls = [params for endpoint, params in executor.calls if endpoint == "opt_daily"]
    assert len(calls) == 2 and [params["offset"] for params in calls] == [0, len(executor.daily)]
    assert calls[0]["start_date"] == "20240102" and calls[0]["end_date"] == "20240104"
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT count(*) FROM basis_snapshot").fetchone()[0] == 1


def test_small_window_shares_cross_section_across_products_and_releases_response(
    setup: Any,
) -> None:
    service, _, executor, _ = setup
    other = deepcopy(executor.catalog)
    for item in other:
        item["ts_code"] = item["ts_code"].replace("IO", "HO")
        item["symbol"] = item["symbol"].replace("IO", "HO")
        item["opt_code"] = "OP000016.SH"
    executor.catalog.extend(other)
    executor.daily = [
        dict(daily(meta), trade_date=(DAY + timedelta(days=index)).strftime("%Y%m%d"))
        for index in range(4)
        for meta in executor.catalog
    ]
    source = _source.DailySource(executor)
    service._source_factory = lambda: source
    result = service.ensure(public.OptionsDailyRange(["IO", "HO"], DAY, DAY + timedelta(days=3)))
    assert result.complete and result.succeeded_units == 8
    daily_calls = [params for endpoint, params in executor.calls if endpoint == "opt_daily"]
    assert len(daily_calls) == 4
    assert not source.daily_cache


def test_basis_validation_reuse_is_operation_local_but_records_still_checked(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, executor, _ = setup
    original = deepcopy(executor.daily)
    executor.daily += [dict(row, trade_date="20240103") for row in original]
    count = 0
    validate = _source.validated_catalog

    def tracked(product: str, basis: object) -> dict:
        nonlocal count
        count += 1
        return validate(product, basis)

    monkeypatch.setattr(_source, "validated_catalog", tracked)
    request = public.OptionsDailyRange(["IO"], DAY, DAY + timedelta(days=1))
    assert service.ensure(request).complete
    assert count == 2  # Once on fetched facts, once on the committed read snapshot.
    count = 0
    assert service.coverage(request).complete
    assert count == 1
    assert service.coverage(request).complete
    assert count == 2  # A new operation must independently validate its frozen basis.


def test_known_catalog_failure_does_not_issue_unusable_daily_requests(setup: Any) -> None:
    service, _, executor, _ = setup
    executor.catalog[0]["name"] = None
    result = service.ensure(public.OptionsDailyRange(["IO"], DAY, DAY + timedelta(days=2)))
    assert result.attempted_units == 3 and result.failed_units == 3
    assert not any(endpoint.endswith("daily") for endpoint, _ in executor.calls)


def test_sparse_pending_dates_do_not_expand_transport_window_across_months() -> None:
    days = (date(2024, 1, 2), date(2024, 6, 2), date(2025, 1, 2))
    units = tuple(Unit(("IO", day)) for day in days)
    groups = tuple(_service.batches(units))
    assert groups == tuple((unit,) for unit in units)


def test_export_reuses_each_validated_row_only_within_its_snapshot(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, _, request = setup
    assert service.ensure(request).complete
    calls = 0
    original = _source.read_row

    def tracked(record: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(record)

    monkeypatch.setattr(_source, "read_row", tracked)
    first = service.export(request)
    assert calls == len(first.records)
    assert service.export(request) == first
    assert calls == 2 * len(first.records)
    assert service.coverage(request).complete
    assert calls == 3 * len(first.records)


def test_lifecycle_index_preserves_inclusive_edges_and_out_of_order_dates() -> None:
    catalog = {
        "a": {"list_date": "2024-01-02", "delist_date": "2024-01-03"},
        "b": {"list_date": "2024-01-03", "delist_date": "2024-01-03"},
        "c": {"list_date": "2024-01-04", "delist_date": "2024-01-05"},
    }
    index = _source.ContractIndex(catalog)
    for offset in (0, 1, 2, 3, 4, 1, 0, 3, 2):
        target = DAY + timedelta(days=offset)
        expected = {
            code: meta
            for code, meta in catalog.items()
            if meta["list_date"] <= target.isoformat() <= meta["delist_date"]
        }
        assert index.at(target) == expected


@pytest.mark.parametrize("unowned", [False, True])
def test_malformed_cross_section_is_isolated_by_product_and_day(
    setup: Any,
    unowned: bool,
) -> None:
    service, _, executor, _ = setup
    family = "IO"
    other_family = "HO"
    other = deepcopy(executor.catalog)
    for item in other:
        item["ts_code"] = item["ts_code"].replace(family, other_family)
        item["symbol"] = item["symbol"].replace(family, other_family)
        item["opt_code"] = "OP000016.SH"
    executor.catalog.extend(other)
    executor.daily = [
        dict(daily(meta), trade_date=(DAY + timedelta(days=n)).strftime("%Y%m%d"))
        for n in range(2)
        for meta in executor.catalog
    ]
    # An extra malformed row must not disappear during the initial product split.
    executor.daily.append(dict(executor.daily[0], ts_code="bad" if unowned else family + "bad"))
    request = public.OptionsDailyRange([family, other_family], DAY, DAY + timedelta(days=1))
    result = service.ensure(request)
    assert result.failed_units == (2 if unowned else 1)
    assert {failure.identity for failure in result.failures} == (
        {(family, DAY), (other_family, DAY)} if unowned else {(family, DAY)}
    )
    assert result.succeeded_units + result.failed_units == 4
