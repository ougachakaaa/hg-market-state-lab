"""Public runtime, strong completeness and owned snapshots using isolated Source facts."""

import sqlite3
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from data_lake import InvalidRequestError, OperationError
from data_lake.adapters.outbound.sqlite import Repository
from data_lake.datasets import tushare_index_daily as public
from data_lake.datasets.tushare_index_daily import _composition, _domain, _service, _source
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar._service import _create_service as calendar_create
from data_lake.datasets.tushare_trade_calendar._source import TradeCalSource
from data_lake.domain import ExecutionFailure, Unit

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
        if endpoint == "index_basic" and params["market"] != "SSE":
            return Frame([])
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
    return [
        dict(
            ts_code="000300.SH",
            name="index",
            market="SSE",
            publisher=None,
            category="composite",
            list_date="20050101",
            exp_date=None,
        )
    ]


def daily(meta: dict[str, Any]) -> dict[str, Any]:
    return dict(
        ts_code=meta["ts_code"],
        trade_date="20240102",
        open=1,
        high=2,
        low=1,
        close=2,
        pre_close=1,
        change=1,
        pct_chg=100,
        vol=0,
        amount=0,
    )


@pytest.fixture
def setup(tmp_path: Path) -> tuple[Any, Repository, Executor, Any]:
    executor = Executor()
    calendar = calendar_create(
        Repository(tmp_path / "calendar.sqlite3", "tushare_trade_calendar", "tushare"),
        lambda: TradeCalSource(executor),
    )
    repo = Repository(tmp_path / "owned.sqlite3", "tushare_index_daily", "tushare")
    service = _service._create_service(repo, calendar, lambda: _source.DailySource(executor, {}))
    request = public.IndexDailyRange(["000300.SH"], DAY, DAY)
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
    assert view.dataset == "tushare_index_daily"
    assert type(view.records[0].trade_date) is date
    before = repo.path.read_bytes()
    calls = len(executor.calls)
    assert service.coverage(request).complete
    assert service.ensure(request).attempted_units == 0
    assert service.export(request).coverage.complete
    assert repo.path.read_bytes() == before and len(executor.calls) == calls
    cached = repo.snapshot((Unit(("000300.SH", DAY)),)).successful[0]
    assert cached.basis is not None
    assert len(cached.records) == len(executor.daily)
    assert "__all__" not in vars(public)
    for name in (
        "IndexDailyService",
        "IndexDailyRange",
        "IndexDailyRow",
        "IndexDailyExport",
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
        extra["ts_code"] = "000905.SH"
        executor.daily = [extra]
    elif defect == "field":
        executor.daily[0].pop("close")
    else:
        executor.daily[0]["close"] = {"invalid": None, "nan": float("nan"), "boolean": True}[defect]
    result = service.ensure(request)
    assert not result.complete and result.failed_units == 1 and result.records_written == 0
    assert result.failures[0].identity == ("000300.SH", DAY)
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
    service._calendar.ensure(TradeCalendarRange("SSE", DAY, DAY))
    calls = len(executor.calls)
    assert service.coverage(request).missing_units == 1
    assert service.export(request).records == ()
    assert not repo.path.exists() and len(executor.calls) == calls


@pytest.mark.parametrize("values", [[], "000300.SH", ["bad"], [None]])
def test_invalid_request_before_dependency(values: Any) -> None:
    with pytest.raises(InvalidRequestError):
        public.IndexDailyRange(values, DAY, DAY)


def test_catalog_failure_is_unit_failure_and_retry_succeeds(setup: Any) -> None:
    service, _, executor, request = setup
    service._calendar.ensure(TradeCalendarRange("SSE", DAY, DAY))
    executor.error = True
    assert service.ensure(request).failed_units == 1
    executor.error = False
    assert service.ensure(request).complete


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
        unit = Unit(("000300.SH", DAY))
        repo.pending(unit)
        repo.failed(unit, ExecutionFailure("concurrent mutation"))
        return result

    monkeypatch.setattr(repo, "snapshot", capture)
    view = service.export(request)
    assert len(snapshots) == 1 and view.coverage.complete
    assert len(view.records) == len(executor.daily)
    assert original((Unit(("000300.SH", DAY)),)).coverage.failed_units == 1


def test_no_trading_days_skips_source_and_storage(
    setup: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, repo, executor, request = setup
    assert service._calendar.ensure(TradeCalendarRange("SSE", DAY, DAY)).complete
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
    request = public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=1))
    result = service.ensure(request)
    assert (result.requested_units, result.succeeded_units, result.failed_units) == (2, 1, 1)
    view = service.export(request)
    assert not view.coverage.complete and view.coverage.successful_units == 1
    assert len(view.records) == len(executor.daily)


def test_local_metadata_reused_for_new_date(setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, executor, request = setup
    assert service.ensure(request).complete
    next_day = DAY + timedelta(days=1)
    executor.daily[0]["trade_date"] = "20240103"
    original = executor.call

    def call(endpoint: str, **params: Any) -> Any:
        if endpoint == "index_basic":
            pytest.fail("legal local metadata should be reused")
        return original(endpoint, **params)

    monkeypatch.setattr(executor, "call", call)
    monkeypatch.setattr(executor, "prepare", lambda: executor, raising=False)
    monkeypatch.setattr(_composition, "TushareExecutor", lambda: executor)
    service._source_factory = service._prepare
    assert service.ensure(public.IndexDailyRange(["000300.SH"], next_day, next_day)).complete


def test_sh_suffix_can_belong_to_csi_market(setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, executor, request = setup
    original = executor.call
    executor.catalog[0]["market"] = "CSI"

    def call(endpoint: str, **params: Any) -> Any:
        if endpoint == "index_basic":
            executor.calls.append((endpoint, params))
            return Frame(
                executor.catalog[int(params["offset"]) :] if params["market"] == "CSI" else []
            )
        return original(endpoint, **params)

    monkeypatch.setattr(executor, "call", call)
    assert service.ensure(request).complete
    assert service.export(request).records[0].market == "CSI"


def test_factory_owns_colocated_storage_without_source(monkeypatch: pytest.MonkeyPatch) -> None:
    from data_lake.providers.tushare import _executor

    monkeypatch.setattr(
        _executor, "resolve_credential", lambda: pytest.fail("factory must be lazy")
    )
    dataset_root = Path(__file__).resolve().parents[1]
    expected = dataset_root / "data" / (dataset_root.name + ".sqlite3")
    existed = expected.exists()
    service = public.create_service()
    assert cast(Repository, service._repository).path == expected
    assert expected.exists() == existed


def test_other_addressable_index_rows_are_not_written(setup: Any) -> None:
    service, _, executor, request = setup
    unrelated = dict(executor.daily[0], ts_code="000905.SH")
    executor.daily.append(unrelated)
    assert service.ensure(request).complete
    assert [row.index_code for row in service.export(request).records] == ["000300.SH"]


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
def test_future_window_rejected_before_dependency_or_source(setup: Any, operation: str) -> None:
    service, repo, executor, request = setup
    object.__setattr__(request, "end_date", date(9999, 12, 31))
    with pytest.raises(InvalidRequestError, match="today"):
        getattr(service, operation)(request)
    assert not executor.calls and not repo.path.exists()
    with pytest.raises(InvalidRequestError, match="today"):
        public.IndexDailyRange(["000300.SH"], DAY, date(9999, 12, 31))


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
    request = public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=2))
    result = service.ensure(request)
    assert (result.attempted_units, result.succeeded_units, result.failed_units) == (3, 2, 1)
    assert result.failures[0].identity == ("000300.SH", DAY + timedelta(days=1))
    view = service.export(request)
    assert {row.trade_date for row in view.records} == {DAY, DAY + timedelta(days=2)}
    calls = [params for endpoint, params in executor.calls if endpoint == "index_daily"]
    assert len(calls) == 2 and [params["offset"] for params in calls] == [0, len(executor.daily)]
    assert calls[0]["start_date"] == "20240102" and calls[0]["end_date"] == "20240104"
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT count(*) FROM basis_snapshot").fetchone()[0] == 1


def test_known_catalog_failure_does_not_issue_unusable_daily_requests(setup: Any) -> None:
    service, _, executor, _ = setup
    executor.catalog[0]["name"] = None
    result = service.ensure(public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=2)))
    assert result.attempted_units == 3 and result.failed_units == 3
    assert not any(endpoint.endswith("daily") for endpoint, _ in executor.calls)


def test_export_reuses_each_validated_row_only_within_its_snapshot(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, _, request = setup
    assert service.ensure(request).complete
    calls = 0
    original = _domain.read_row

    def tracked(record: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(record)

    monkeypatch.setattr(_domain, "read_row", tracked)
    first = service.export(request)
    assert calls == len(first.records)
    assert service.export(request) == first
    assert calls == 2 * len(first.records)
    assert service.coverage(request).complete
    assert calls == 3 * len(first.records)


def test_batched_metadata_preserves_code_failures_and_never_requeries_batch(setup: Any) -> None:
    _, _, executor, _ = setup
    good = "000300.SH"
    bad = "000905.SH"
    executor.catalog.append(dict(executor.catalog[0], ts_code=bad, name=None))
    source = _source.DailySource(executor, {}, (good, bad))
    source.fetch((Unit((good, DAY)),))
    basic = [params for endpoint, params in executor.calls if endpoint == "index_basic"]
    assert {p["market"] for p in basic} == {"SSE", "SZSE", "CSI", "CICC", "OTH", "MSCI", "SW"}
    assert all(p["symbol"] == "000300,000905" for p in basic)
    assert good in source.metadata and bad in source.errors
    count = len(executor.calls)
    with pytest.raises(ExecutionFailure):
        source.fetch((Unit((bad, DAY)),))
    assert len(executor.calls) == count


@pytest.mark.parametrize("separate_pages", [False, True])
def test_duplicate_daily_isolated_after_exhaustion(
    setup: Any, monkeypatch: pytest.MonkeyPatch, separate_pages: bool
) -> None:
    service, _, executor, _ = setup
    bad = executor.daily[0]
    good = dict(bad, trade_date="20240103")
    records = [bad, good, deepcopy(bad)]
    original = executor.call

    def call(endpoint: str, **params: Any) -> Frame:
        if endpoint != "index_daily":
            return original(endpoint, **params)
        executor.calls.append((endpoint, params))
        offset = params["offset"]
        return Frame(records[offset : offset + (2 if separate_pages else 4000)])

    monkeypatch.setattr(executor, "call", call)
    result = service.ensure(public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=1)))
    assert (result.attempted_units, result.succeeded_units, result.failed_units) == (2, 1, 1)
    assert result.records_written == 1
    assert [failure.identity for failure in result.failures] == [("000300.SH", DAY)]
    view = service.export(public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=1)))
    assert [row.trade_date for row in view.records] == [DAY + timedelta(days=1)]
    offsets = [params["offset"] for endpoint, params in executor.calls if endpoint == "index_daily"]
    assert offsets == ([0, 2, 3] if separate_pages else [0, 3])


@pytest.mark.parametrize("separate_pages", [False, True])
def test_duplicate_metadata_isolated_after_exhaustion(
    setup: Any, monkeypatch: pytest.MonkeyPatch, separate_pages: bool
) -> None:
    service, _, executor, _ = setup
    good, bad = "000300.SH", "000905.SH"
    bad_meta = dict(executor.catalog[0], ts_code=bad)
    records = [bad_meta, executor.catalog[0], deepcopy(bad_meta)]
    original = executor.call

    def call(endpoint: str, **params: Any) -> Frame:
        if endpoint != "index_basic":
            return original(endpoint, **params)
        executor.calls.append((endpoint, params))
        offset = params["offset"]
        return Frame(
            records[offset : offset + (2 if separate_pages else 4000)]
            if params["market"] == "SSE"
            else []
        )

    monkeypatch.setattr(executor, "call", call)
    source = _source.DailySource(executor, {}, (good, bad))
    service._source_factory = lambda: source
    result = service.ensure(public.IndexDailyRange([good, bad], DAY, DAY))
    assert (result.attempted_units, result.succeeded_units, result.failed_units) == (2, 1, 1)
    assert result.records_written == 1
    assert [failure.identity for failure in result.failures] == [(bad, DAY)]
    assert set(source.metadata) == {good} and set(source.errors) == {bad}
    daily_codes = [
        params["ts_code"] for endpoint, params in executor.calls if endpoint == "index_daily"
    ]
    assert daily_codes == [good, good]
    count = len(executor.calls)
    with pytest.raises(ExecutionFailure):
        source.fetch((Unit((bad, DAY)),))
    assert len(executor.calls) == count


def test_repeated_daily_page_still_fails_entire_batch(
    setup: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, _, executor, _ = setup
    original = executor.call
    page = [executor.daily[0], dict(executor.daily[0], trade_date="20240103")]

    def call(endpoint: str, **params: Any) -> Frame:
        if endpoint != "index_daily":
            return original(endpoint, **params)
        executor.calls.append((endpoint, params))
        return Frame(page)

    monkeypatch.setattr(executor, "call", call)
    result = service.ensure(public.IndexDailyRange(["000300.SH"], DAY, DAY + timedelta(days=1)))
    assert (result.succeeded_units, result.failed_units, result.records_written) == (0, 2, 0)
    assert all("repeated a page" in failure.reason for failure in result.failures)


def test_metadata_reuse_selects_latest_representative_for_requested_code(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repo, executor, request = setup
    executor.catalog.append(dict(executor.catalog[0], ts_code="000905.SH"))
    executor.daily = [
        dict(daily(meta), trade_date=(DAY + timedelta(days=n)).strftime("%Y%m%d"))
        for n in range(3)
        for meta in executor.catalog
    ]
    assert service.ensure(
        public.IndexDailyRange(["000300.SH", "000905.SH"], DAY, DAY + timedelta(days=2))
    ).complete
    captured = []
    original = repo.snapshot

    def tracked(units: Any) -> Any:
        captured.append(tuple(units))
        return original(units)

    monkeypatch.setattr(repo, "snapshot", tracked)
    monkeypatch.setattr(executor, "prepare", lambda: executor, raising=False)
    monkeypatch.setattr(_composition, "TushareExecutor", lambda: executor)
    source = service._prepare(request.index_codes)
    assert captured == [(Unit(("000300.SH", DAY + timedelta(days=2))),)]
    assert set(source.metadata) == {"000300.SH"}


def test_metadata_batches_bound_symbols_and_check_cross_market_conflicts(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, executor, _ = setup
    codes = tuple(f"{n:06}.SH" for n in range(100, 165))
    executor.catalog = [dict(catalog()[0], ts_code=code) for code in codes]

    def call(endpoint: str, **params: Any) -> Frame:
        executor.calls.append((endpoint, params))
        wanted = set(params["symbol"].split(","))
        rows = [row for row in executor.catalog if row["ts_code"][:6] in wanted]
        return Frame(rows[int(params["offset"]) :] if params["market"] == "SSE" else [])

    monkeypatch.setattr(executor, "call", call)
    source = _source.DailySource(executor, {}, codes)
    source._load_metadata(codes[0])
    assert len(source.metadata) == 64
    source._load_metadata(codes[-1])
    assert set(source.metadata) == set(codes)
    assert max(len(params["symbol"].split(",")) for _, params in executor.calls) == 64
    assert len(executor.calls) == 16
    # A duplicate identity in another market cannot be accepted by stopping early.
    executor.calls.clear()
    duplicate = dict(executor.catalog[0], market="CSI")

    def conflict(endpoint: str, **params: Any) -> Frame:
        executor.calls.append((endpoint, params))
        rows = [duplicate] if params["market"] == "CSI" else executor.catalog[:2]
        return Frame(rows[int(params["offset"]) :] if params["market"] in ("SSE", "CSI") else [])

    monkeypatch.setattr(executor, "call", conflict)
    source = _source.DailySource(executor, {}, codes[:2])
    with pytest.raises(ExecutionFailure):
        source._load_metadata(codes[0])
    assert codes[1] in source.metadata and codes[0] in source.errors


def test_metadata_transport_failure_fails_batch_without_daily_calls(setup: Any) -> None:
    _, _, executor, _ = setup
    codes = ("000300.SH", "000905.SH")
    executor.error = True
    source = _source.DailySource(executor, {}, codes)
    for code in codes:
        with pytest.raises(ExecutionFailure):
            source.fetch((Unit((code, DAY)),))
    assert set(source.errors) == set(codes)
    assert [endpoint for endpoint, _ in executor.calls] == ["index_basic"]


def test_metadata_reuse_does_not_fall_back_from_corrupt_latest_representative(
    setup: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repo, executor, request = setup
    executor.daily += [dict(executor.daily[0], trade_date="20240103")]
    assert service.ensure(
        public.IndexDailyRange(request.index_codes, DAY, DAY + timedelta(days=1))
    ).complete
    with sqlite3.connect(repo.path) as connection:
        connection.execute(
            "UPDATE fetch_unit SET content_hash='corrupt' WHERE unit_key=?",
            (Unit(("000300.SH", DAY + timedelta(days=1))).key,),
        )
    monkeypatch.setattr(
        _composition,
        "TushareExecutor",
        lambda: pytest.fail("invalid metadata must fail before Source initialization"),
    )
    with pytest.raises(OperationError, match="metadata"):
        service._prepare(request.index_codes)
