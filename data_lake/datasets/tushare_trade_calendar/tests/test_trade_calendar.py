"""Calendar authority invariants exercised without external credentials or I/O."""

import inspect
import sqlite3
from dataclasses import asdict, fields
from datetime import date, datetime
from pathlib import Path
from typing import cast

import pytest

import data_lake
from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError
from data_lake._serialization import Json, record_hash
from data_lake.adapters.outbound.sqlite import Repository
from data_lake.datasets import tushare_trade_calendar as public
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarRange,
    TradeCalendarService,
    _composition,
    _service,
    _source,
)
from data_lake.datasets.tushare_trade_calendar._domain import DATASET, targets
from data_lake.datasets.tushare_trade_calendar._models import CalendarWindow, TradeCalendarScope
from data_lake.datasets.tushare_trade_calendar._service import _create_service
from data_lake.datasets.tushare_trade_calendar._source import TradeCalSource
from data_lake.domain import ExecutionFailure, Record, UnitRecords
from data_lake.providers.tushare import _executor

DAY = date(2024, 1, 1)
REQUEST = TradeCalendarRange("SSE", DAY, date(2024, 1, 3))


def row(day: str = "20240101", **changes: object) -> dict[str, object]:
    return {
        "exchange": "SSE",
        "cal_date": day,
        "is_open": "0",
        "pretrade_date": "20231229",
        **changes,
    }


class Frame:
    def __init__(self, rows: object) -> None:
        self.rows = rows

    def to_dict(self, *, orient: str) -> object:
        assert orient == "records"
        return self.rows


class Client:
    def call(self, endpoint: str, **kwargs: str) -> object:
        try:
            return getattr(self, endpoint)(**kwargs)
        except Exception as exc:
            raise ExecutionFailure("Tushare provider request failed", "source_request") from exc

    def __init__(self) -> None:
        self.rows: object = []
        self.calls: list[dict[str, str]] = []
        self.error: Exception | None = None

    def trade_cal(self, **kwargs: str) -> Frame:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return Frame(self.rows)


@pytest.fixture
def setup(tmp_path: Path) -> tuple[TradeCalendarService, Repository, Client]:
    repository = Repository(tmp_path / "cache/calendar.sqlite3", DATASET, "tushare")
    client = Client()
    return _create_service(repository, lambda: TradeCalSource(client)), repository, client


@pytest.mark.parametrize(
    "changes",
    [
        {"exchange": ""},
        {"exchange": " SSE"},
        {"exchange": "SSE "},
        {"exchange": "S SE"},
        {"exchange": None},
        {"exchange": 1},
        {"start_date": "2024-01-01"},
        {"start_date": datetime(2024, 1, 1)},
        {"end_date": None},
        {"end_date": date(2023, 12, 31)},
    ],
)
def test_semantic_validation(changes: dict[str, object]) -> None:
    values = {"exchange": "SSE", "start_date": DAY, "end_date": DAY, **changes}
    with pytest.raises(InvalidRequestError):
        TradeCalendarRange(**values)  # type: ignore[arg-type]


def test_no_enum_or_case_normalization() -> None:
    assert TradeCalendarRange("provider_native", DAY, DAY).exchange == "provider_native"


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
def test_wrong_request_is_public_invalid_request(
    setup: tuple[TradeCalendarService, Repository, Client],
    operation: str,
) -> None:
    service, repository, client = setup
    with pytest.raises(InvalidRequestError):
        getattr(service, operation)(None)
    assert not repository.path.parent.exists() and not client.calls


def test_inclusive_units_and_exchange_identity() -> None:
    units = targets(REQUEST)
    assert [unit.identity for unit in units] == [
        ("SSE", DAY),
        ("SSE", date(2024, 1, 2)),
        ("SSE", date(2024, 1, 3)),
    ]
    assert units[0].key != targets(TradeCalendarRange("SZSE", DAY, DAY))[0].key
    assert targets(TradeCalendarRange("SSE", date.max, date.max))[0].identity == ("SSE", date.max)


def test_missing_cache_reads_and_factory_are_lazy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _composition, "database_path", lambda *_: tmp_path / "cache/calendar.sqlite3"
    )

    def forbidden() -> None:
        pytest.fail("read operations cannot resolve credentials")

    monkeypatch.setattr(_service, "prepare_source", forbidden)
    service = public.create_service()
    assert service.coverage(REQUEST) == CoverageResult(3, 0, 3, 0, 0, False)
    view = service.export(REQUEST)
    assert view.coverage == service.coverage(REQUEST) and view.records == ()
    assert not (tmp_path / "cache").exists()


def test_factory_resolves_owned_storage_without_creating_it() -> None:
    service = public.create_service()
    assert cast(Repository, service._core._repository).path == (
        Path(__file__).resolve().parents[1] / "data/tushare_trade_calendar.sqlite3"
    )


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
def test_validation_execution_failure_remains_an_operation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    repository = Repository(tmp_path / "calendar.sqlite3", DATASET, "tushare")
    service = _create_service(repository, lambda: pytest.fail("validation must precede Source"))
    request = TradeCalendarRange("SSE", DAY, DAY)

    def broken_validation(request: TradeCalendarRange) -> None:
        raise RuntimeError("Unexpected validation failure")

    monkeypatch.setattr(TradeCalendarRange, "__post_init__", broken_validation)
    with pytest.raises(OperationError, match=f"{operation.title()} operation"):
        getattr(service, operation)(request)
    assert not repository.path.exists()


def test_legacy_cache_is_untouched_and_never_used_as_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Exercise the real default composition in a temporary repository layout.
    lake = tmp_path / "data_lake"
    legacy_root = lake / "data"
    legacy = Repository(legacy_root / "tushare_trade_calendar.sqlite3", DATASET, "tushare")
    old_client = Client()
    old_client.rows = [row()]
    request = TradeCalendarRange("SSE", DAY, DAY)
    assert _create_service(legacy, lambda: TradeCalSource(old_client)).ensure(request).complete
    (legacy_root / "unrelated.sqlite3").write_bytes(b"untouched legacy state")
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in legacy_root.iterdir()
    }

    dataset_root = lake / "datasets/tushare_trade_calendar"
    monkeypatch.setattr(
        _composition,
        "__file__",
        str(dataset_root / "src/data_lake/datasets/tushare_trade_calendar/_composition.py"),
    )
    client = Client()
    client.rows = [row(is_open=1)]
    monkeypatch.setattr(_service, "prepare_source", lambda: TradeCalSource(client))
    original_connect = sqlite3.connect

    def connect(database: object, *args: object, **kwargs: object) -> sqlite3.Connection:
        assert "tushare_trade_calendar.sqlite3" not in str(database) or (
            "datasets" in str(database)
        ), "legacy cache must not be opened"
        return original_connect(database, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(sqlite3, "connect", connect)
    service = public.create_service()
    owned = dataset_root / "data/tushare_trade_calendar.sqlite3"
    assert cast(Repository, service._core._repository).path == owned
    assert service.coverage(request) == CoverageResult(1, 0, 1, 0, 0, False)
    assert service.export(request).records == ()
    assert not owned.parent.exists() and not client.calls

    assert service.ensure(request).complete
    assert owned.is_file() and len(client.calls) == 1
    assert service.export(request).records[0].is_open == 1
    # Both paths now exist; reopening still uses only the new local cache.
    cached = public.create_service()
    assert cached.ensure(request) == EnsureResult(1, 1, 0, 0, 0, 0, True, ())
    assert cached.coverage(request).complete
    assert cached.export(request).records[0].is_open == 1
    assert len(client.calls) == 1
    assert before == {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in legacy_root.iterdir()
    }


def test_first_fill_existing_success_skip_and_export(
    setup: tuple[TradeCalendarService, Repository, Client],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository, client = setup
    client.rows = [
        row("20240103", is_open=1, pretrade_date="20240102"),
        row(),
        row("20240102", is_open=1, pretrade_date=None),
    ]
    assert service.ensure(REQUEST) == EnsureResult(3, 0, 3, 3, 0, 3, True, ())
    assert client.calls == [
        {
            "exchange": "SSE",
            "start_date": "20240101",
            "end_date": "20240103",
            "fields": "exchange,cal_date,is_open,pretrade_date",
        }
    ]
    view = service.export(REQUEST)
    assert view.dataset == DATASET and view.view == "calendar"
    assert type(view.export_schema_version) is int and view.export_schema_version == 1
    assert view.scope.exchange == "SSE"
    assert (view.window.start_date, view.window.end_date) == (REQUEST.start_date, REQUEST.end_date)
    assert [record.cal_date for record in view.records] == [DAY, date(2024, 1, 2), date(2024, 1, 3)]
    assert all(type(record.is_open) is int for record in view.records)
    assert view.records[1].pretrade_date is None
    assert service.coverage(TradeCalendarRange("SZSE", DAY, DAY)).missing_units == 1
    before = repository.path.read_bytes(), repository.path.stat().st_mtime_ns

    def forbidden() -> None:
        pytest.fail("fully cached ensure cannot initialize Source")

    monkeypatch.setattr(service._core, "_prepare_source", forbidden)
    assert service.ensure(REQUEST) == EnsureResult(3, 3, 0, 0, 0, 0, True, ())
    service.coverage(REQUEST)
    service.export(REQUEST)
    assert before == (repository.path.read_bytes(), repository.path.stat().st_mtime_ns)
    with sqlite3.connect(repository.path) as connection:
        assert connection.execute("SELECT count(*) FROM instrument").fetchone()[0] == 0
        assert connection.execute("SELECT record_count FROM fetch_unit").fetchall() == [(1,)] * 3


def test_partial_missing_retry_and_outside_targets(
    setup: tuple[TradeCalendarService, Repository, Client],
) -> None:
    service, repository, client = setup
    client.rows = [row(), row("20240103", is_open=2), row("20240104")]
    result = service.ensure(REQUEST)
    assert (
        result.attempted_units,
        result.succeeded_units,
        result.failed_units,
        result.records_written,
        result.complete,
    ) == (3, 1, 2, 1, False)
    assert [failure.identity for failure in result.failures] == [
        ("SSE", date(2024, 1, 2)),
        ("SSE", date(2024, 1, 3)),
    ]
    view = service.export(REQUEST)
    assert view.coverage == CoverageResult(3, 1, 0, 0, 2, False)
    assert len(view.records) == 1
    assert service.coverage(TradeCalendarRange("SSE", date(2024, 1, 4), date(2024, 1, 4))) == (
        CoverageResult(1, 0, 1, 0, 0, False)
    )
    # Already-successful row in a range response must not rewrite its owned facts.
    client.rows = [row(is_open=1), row("20240102"), row("20240103")]
    assert service.ensure(REQUEST) == EnsureResult(3, 1, 2, 2, 0, 2, True, ())
    assert service.export(REQUEST).records[0].is_open == 0
    assert service.export(REQUEST).records[0] == view.records[0]


@pytest.mark.parametrize(
    "rows",
    [
        [row(), row()],
        [row(), row(is_open=1)],
        [row(exchange="SZSE")],
        [row(is_open=True)],
        [row(is_open=0.0)],
        [row(is_open=None)],
        [row(is_open=" 1")],
        [row(pretrade_date="20240230")],
        [row(pretrade_date="invalid")],
        [row(pretrade_date=0)],
        [{key: value for key, value in row().items() if key != "pretrade_date"}],
    ],
)
def test_invalid_target_is_failed_without_poisoning_other_dates(
    setup: tuple[TradeCalendarService, Repository, Client],
    rows: list[dict[str, object]],
) -> None:
    service, _, client = setup
    client.rows = rows + [row("20240102"), row("20240103")]
    result = service.ensure(REQUEST)
    assert (result.succeeded_units, result.failed_units, result.records_written) == (2, 1, 2)
    assert result.failures[0].identity == ("SSE", DAY)
    assert len(service.export(REQUEST).records) == 2


@pytest.mark.parametrize(
    "rows",
    [
        [row(cal_date="20240230")],
        [row(cal_date=None)],
        [row(cal_date="2024-01-01")],
        [None],
        {},
    ],
)
def test_unpartitionable_response_cannot_attest_to_success(
    setup: tuple[TradeCalendarService, Repository, Client],
    rows: object,
) -> None:
    service, _, client = setup
    client.rows = rows
    result = service.ensure(REQUEST)
    assert result.failed_units == 3 and result.succeeded_units == 0
    assert len(result.failures) == 3 and service.export(REQUEST).records == ()


@pytest.mark.parametrize("absent", [None, "", float("nan")])
def test_source_null_representation(
    setup: tuple[TradeCalendarService, Repository, Client],
    absent: object,
) -> None:
    service, _, client = setup
    client.rows = [row(pretrade_date=absent)]
    request = TradeCalendarRange("SSE", DAY, DAY)
    assert service.ensure(request).complete
    assert service.export(request).records[0].pretrade_date is None


def test_provider_request_failure_is_safe_unit_result(
    setup: tuple[TradeCalendarService, Repository, Client],
) -> None:
    service, _, client = setup
    client.error = RuntimeError("private token and provider response")
    result = service.ensure(REQUEST)
    assert result.failed_units == 3
    assert all(failure.reason == "Tushare provider request failed" for failure in result.failures)


def test_missing_credentials_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    monkeypatch.setattr(_executor, "dotenv_values", lambda _: {})
    repository = Repository(tmp_path / "cache/calendar.sqlite3", DATASET, "tushare")
    service = _create_service(repository, _source.prepare_source)
    with pytest.raises(OperationError, match="credential"):
        service.ensure(REQUEST)
    assert not repository.path.parent.exists()


def test_cached_ensure_without_token_uses_real_lazy_composition(
    setup: tuple[TradeCalendarService, Repository, Client],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository, client = setup
    client.rows = [row(), row("20240102"), row("20240103")]
    assert service.ensure(REQUEST).complete
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    monkeypatch.setattr(_executor, "dotenv_values", lambda _: {})
    cached = _create_service(repository, _source.prepare_source)
    assert cached.ensure(REQUEST) == EnsureResult(3, 3, 0, 0, 0, 0, True, ())


def test_actual_dataframe_normalization(
    setup: tuple[TradeCalendarService, Repository, Client],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pandas

    service, _, client = setup
    frame = pandas.DataFrame(
        [row(is_open=0, pretrade_date=float("nan")), row("20240102", is_open=1)]
    )
    monkeypatch.setattr(client, "trade_cal", lambda **kwargs: frame)
    result = service.ensure(REQUEST)
    assert (result.succeeded_units, result.failed_units, result.records_written) == (2, 1, 2)
    records = service.export(REQUEST).records
    assert records[0].pretrade_date is None
    assert all(type(record.is_open) is int for record in records)


@pytest.mark.parametrize("environment", ["environment-token", "", None])
def test_environment_precedence_and_snapshot_env_fallback(
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(_executor, "_states", {})
    if environment is None:
        monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    else:
        monkeypatch.setenv("TUSHARE_TOKEN", environment)

    def dotenv(path: Path) -> dict[str, str]:
        calls.append(path)
        return {"TUSHARE_TOKEN": "fallback-token"}

    monkeypatch.setattr(_executor, "dotenv_values", dotenv)
    client = Client()

    def pro_api(token: str) -> Client:
        calls.append(token)
        return client

    monkeypatch.setattr(_executor, "create_client", pro_api)
    if environment == "":
        with pytest.raises(OperationError):
            _source.prepare_source()
        assert calls == []
    else:
        _source.prepare_source()
        if environment is None:
            assert calls == [
                Path(__file__).resolve().parents[4] / "data_snapshot/.env",
                "fallback-token",
            ]
        else:
            assert calls == [environment]


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
@pytest.mark.parametrize("kind", ["zero", "duplicate", "identity", "fact", "instrument"])
def test_semantically_corrupt_success_is_operation_error(
    setup: tuple[TradeCalendarService, Repository, Client],
    operation: str,
    kind: str,
) -> None:
    service, repository, client = setup
    client.rows = [row()]
    request = TradeCalendarRange("SSE", DAY, DAY)
    service.ensure(request)
    unit = targets(request)[0]
    record = repository.snapshot((unit,)).successful[0].records[0]
    if kind == "zero":
        facts = UnitRecords(())
    elif kind == "duplicate":
        facts = UnitRecords((record, record))
    else:
        changes_by_kind: dict[str, dict[str, Json]] = {
            "identity": {"exchange": "SZSE"},
            "fact": {"is_open": True},
            "instrument": {},
        }
        facts = UnitRecords((Record({**record.fields, **changes_by_kind[kind]}),))
    repository.pending(unit)
    repository.succeed(unit, facts)
    if kind == "instrument":
        with sqlite3.connect(repository.path) as connection:
            connection.execute("INSERT INTO instrument(instrument_key) VALUES ('invalid')")
            connection.execute("UPDATE records SET instrument_id=1")
            connection.execute(
                "UPDATE fetch_unit SET content_hash=?",
                (record_hash([Record(record.fields, "invalid").encode()]),),
            )
    with pytest.raises(OperationError):
        getattr(service, operation)(request)


def test_export_uses_one_snapshot_when_commit_occurs_during_projection(
    setup: tuple[TradeCalendarService, Repository, Client],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository, client = setup
    client.rows = [row()]
    service.ensure(REQUEST)
    original = service._core._project

    def project(request: TradeCalendarRange, coverage: CoverageResult, cached: tuple) -> object:
        repository.pending(targets(REQUEST)[0])
        return original(request, coverage, cached)

    monkeypatch.setattr(service._core, "_project", project)
    view = service.export(REQUEST)
    assert view.coverage.successful_units == len(view.records) == 1
    assert service.coverage(REQUEST).successful_units == 0


def test_year_batches_bound_transport_and_continue_after_failure(
    tmp_path: Path,
) -> None:
    client = Client()
    request = TradeCalendarRange("SSE", date(2023, 12, 31), DAY)

    class YearClient(Client):
        def trade_cal(self, **kwargs: str) -> Frame:
            self.calls.append(kwargs)
            if kwargs["start_date"] == "20231231":
                raise RuntimeError("provider private detail")
            return Frame([row()])

    client = YearClient()
    repository = Repository(tmp_path / "calendar.sqlite3", DATASET, "tushare")
    service = _create_service(repository, lambda: TradeCalSource(client))
    result = service.ensure(request)
    assert (result.succeeded_units, result.failed_units) == (1, 1)
    assert len(client.calls) == 2


def test_public_import_surface_and_semantic_objects() -> None:
    for name in (
        "TradeCalendarService",
        "TradeCalendarRange",
        "TradeCalendarRecord",
        "TradeCalendarExport",
        "create_service",
    ):
        assert hasattr(public, name)
    for name in (
        "InvalidRequestError",
        "OperationError",
        "CoverageResult",
        "EnsureResult",
        "UnitFailure",
    ):
        assert hasattr(data_lake, name)
    assert not hasattr(data_lake, "ApplicationFailure")
    assert not hasattr(public, "__all__") and not hasattr(data_lake, "__all__")
    for name in ("Repository", "Source", "Core", "database_path", "_create_service"):
        assert not hasattr(public, name)
    assert not inspect.signature(public.create_service).parameters
    assert not inspect.signature(public.TradeCalendarService).parameters
    assert [field.name for field in fields(public.TradeCalendarRecord)] == [
        "exchange",
        "cal_date",
        "is_open",
        "pretrade_date",
    ]
    view = public.TradeCalendarExport(
        DATASET,
        "calendar",
        1,
        TradeCalendarScope("SSE"),
        CalendarWindow(DAY, DAY),
        CoverageResult(1, 0, 1, 0, 0, False),
        (),
    )
    assert asdict(view)["export_schema_version"] == 1


def test_future_calendar_dates_are_not_clamped_and_unpublished_days_remain_retryable(
    setup: tuple[TradeCalendarService, Repository, Client],
) -> None:
    service, repository, client = setup
    request = TradeCalendarRange("SSE", date(9999, 1, 1), date(9999, 1, 2))
    assert service.coverage(request) == CoverageResult(2, 0, 2, 0, 0, False)
    assert not repository.path.exists() and not client.calls
    client.rows = [row("99990101")]
    result = service.ensure(request)
    assert (result.requested_units, result.succeeded_units, result.failed_units) == (2, 1, 1)
    assert service.export(request).records[0].cal_date == date(9999, 1, 1)
    client.rows = [row("99990102")]
    assert service.ensure(request).complete
