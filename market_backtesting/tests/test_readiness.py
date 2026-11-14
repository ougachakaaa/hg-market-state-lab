"""Read-only readiness is advisory coverage, not a successful strategy promise."""

from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from data_lake import CacheIncompatibleError, OperationError
from market_backtesting.cases.futures_roll_long import create_futures_roll_service
from public_input_fixtures import FakeService, fake_services, public_exports, request
from test_public_inputs import incomplete, malformed


class ReadOnlyExport:
    """Deliberately has no ensure, coverage or Source capability."""

    def __init__(self, view: Any) -> None:
        self.view = view
        self.calls: list[Any] = []

    def export(self, value: Any) -> Any:
        self.calls.append(value)
        return self.view


def test_preflight_uses_only_export_and_never_prepares_or_replays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views = public_exports()
    sources = tuple(
        ReadOnlyExport(view) for view in (views.calendar_cffex, views.futures, views.index)
    )
    service = create_futures_roll_service(calendar=sources[0], futures=sources[1], index=sources[2])  # type: ignore[arg-type]

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("preflight cannot prepare, replay or analyze")

    from market_backtesting.cases.futures_roll_long import application

    monkeypatch.setattr(service, "prepare", forbidden)
    monkeypatch.setattr(application, "replay_futures_roll", forbidden)
    monkeypatch.setattr(application, "analyze_futures_roll", forbidden)
    result = service.preflight(request())
    assert result.ready
    assert all(
        item.state == "complete" for item in (result.calendar_cffex, result.futures, result.index)
    )
    assert all(len(source.calls) == 1 for source in sources)


@pytest.mark.parametrize("case", ["close_missing", "index_nan", "invalid_slots"])
def test_ready_does_not_validate_prices_or_promise_strategy_success(case: str) -> None:
    service, *_ = fake_services(malformed(case))
    assert service.preflight(request()).ready


@pytest.mark.parametrize("unavailable", [False, True])
def test_calendar_not_complete_never_queries_downstream(unavailable: bool) -> None:
    views = public_exports()
    service, calendar, futures, index = fake_services()
    calendar.exports = [incomplete(views.calendar_cffex, "calendar_cffex")]
    if unavailable:
        calendar.error = OperationError("unreadable")
    result = service.preflight(request())
    assert not result.ready
    assert result.calendar_cffex.state == ("unavailable" if unavailable else "incomplete")
    assert result.futures.state == result.index.state == "unknown"
    assert not futures.calls and not index.calls


@pytest.mark.parametrize("kind", ["empty", "conflicting", "unavailable"])
def test_unknown_underlying_never_queries_index(kind: str) -> None:
    views = public_exports()
    service, _, futures, index = fake_services()
    if kind == "empty":
        futures.exports = [replace(views.futures, records=())]
    elif kind == "conflicting":
        futures.exports = [malformed("futures_underlying_conflict").futures]
    else:
        futures.error = OperationError("unavailable")
    result = service.preflight(request())
    assert not result.ready
    assert result.index.state == "unknown"
    assert not index.calls


def test_incomplete_futures_can_supply_underlying_without_guessing_dates() -> None:
    views = public_exports()
    service, _, futures, index = fake_services()
    futures.exports = [incomplete(views.futures, "futures")]
    result = service.preflight(request())
    assert result.futures.state == "incomplete"
    assert result.index.state == "complete"
    assert not result.ready
    assert [name for name, _ in futures.calls] == ["export"]
    assert len(index.calls) == 1


@pytest.mark.parametrize("unavailable", [False, True])
def test_index_readiness_states(unavailable: bool) -> None:
    views = public_exports()
    service, _, _, index = fake_services()
    index.exports = [incomplete(views.index, "index")]
    if unavailable:
        index.error = OperationError("unavailable")
    result = service.preflight(request())
    assert not result.ready
    assert result.index.state == ("unavailable" if unavailable else "incomplete")


@pytest.mark.parametrize("missing", ["calendar", "futures", "index"])
def test_real_public_read_paths_do_not_create_cache_or_require_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    """Only test instrumentation touches composition; production uses public factories."""

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("public read path must not initialize Source or require credentials")

    for name in ("tushare_trade_calendar", "tushare_equity_index_futures", "tushare_index_daily"):
        composition = importlib.import_module(f"data_lake.datasets.{name}._composition")
        implementation = importlib.import_module(f"data_lake.datasets.{name}._service")
        monkeypatch.setattr(
            composition,
            "database_path",
            lambda dataset, *_: tmp_path / "absent" / f"{dataset}.sqlite3",
        )
        monkeypatch.setattr(implementation, "prepare_source", forbidden)
    monkeypatch.setenv("TUSHARE_TOKEN", "")
    views = public_exports()

    class CompleteCalendar:
        def export(self, calendar_request: Any) -> Any:
            # Each Dataset still consumes its own declared exchange prerequisite.
            return replace(
                views.calendar_cffex,
                scope=replace(views.calendar_cffex.scope, exchange=calendar_request.exchange),
                records=tuple(
                    replace(row, exchange=calendar_request.exchange)
                    for row in views.calendar_cffex.records
                ),
            )

    if missing != "calendar":
        for name in ("tushare_equity_index_futures", "tushare_index_daily"):
            implementation = importlib.import_module(f"data_lake.datasets.{name}._service")
            monkeypatch.setattr(implementation, "calendar_service", lambda: CompleteCalendar())
    if missing == "calendar":
        service = create_futures_roll_service()
    elif missing == "futures":
        service = create_futures_roll_service(calendar=FakeService(views.calendar_cffex))
    else:
        service = create_futures_roll_service(
            calendar=FakeService(views.calendar_cffex), futures=FakeService(views.futures)
        )
    result = service.preflight(request())
    assert not result.ready
    assert (
        getattr(result, "calendar_cffex" if missing == "calendar" else missing).state
        == "incomplete"
    )
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize(
    "dependency,position", [("calendar_cffex", 0), ("futures", 1), ("index", 2)]
)
def test_cache_incompatible_is_safe_and_does_not_query_downstream(
    dependency: str, position: int
) -> None:
    from dataclasses import asdict

    from market_backtesting.cases.futures_roll_long import FuturesRollApplicationError
    from market_backtesting.cases.futures_roll_long.online_models import project_failure

    service, *sources = fake_services()
    sources[position].error = CacheIncompatibleError("private/path fake-secret")
    result = service.preflight(request())
    item = getattr(result, dependency)
    assert not result.ready
    assert (item.state, item.reason, item.coverage) == ("unavailable", "cache_incompatible", None)
    for downstream in ("calendar_cffex", "futures", "index")[position + 1:]:
        assert getattr(result, downstream).state == "unknown"
    assert all(not source.calls for source in sources[position + 1:])
    assert all(name == "export" for source in sources for name, _ in source.calls)
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert asdict(project_failure(caught.value)) == dict(
        stage="export", category="upstream_operation",
        dependency=dependency, reason="cache_incompatible",
    )
    assert all(not source.calls for source in sources[position + 1:])
