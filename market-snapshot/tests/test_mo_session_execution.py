"""Shared Source budgets, lock boundaries and safe classified retries."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pandas as pd
import pytest
from requests.exceptions import ConnectionError, Timeout

from market_snapshot.sources.session_execution import RequestBudget, SessionExecution
from market_snapshot.sources.tushare import TushareSourceError


def fake_execution() -> tuple[SessionExecution, list[float], list[float]]:
    clock = [1.0]
    waits: list[float] = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        clock[0] += seconds

    return SessionExecution(RequestBudget(clock=lambda: clock[0], sleep=sleep)), clock, waits


def test_budget_shared_across_endpoints_and_network_outside_lock() -> None:
    execution, clock, waits = fake_execution()
    starts: list[float] = []

    def call() -> pd.DataFrame:
        assert execution.budget.lock.acquire(blocking=False)
        execution.budget.lock.release()
        starts.append(clock[0])
        return pd.DataFrame()

    for endpoint in ("opt_basic", "index_daily", "opt_daily", "fut_daily"):
        execution.request(endpoint, call)
    assert starts == pytest.approx([1 + i * 60 / 450 for i in range(4)])
    assert len(waits) == 3
    assert execution.metrics()["attempts"] == 4


@pytest.mark.parametrize(
    "failure", [Timeout("secret"), ConnectionError("secret"), Exception("频率超限 secret")]
)
def test_transient_retry_waits_are_separate_from_response_time(failure: Exception) -> None:
    execution, clock, waits = fake_execution()
    calls = 0

    def call() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        clock[0] += 0.01
        if calls == 1:
            raise failure
        return pd.DataFrame()

    execution.request("opt_daily", call)
    stats = execution.metrics()["endpoints"]["opt_daily"]
    assert stats["attempts"] == 2
    assert stats["retries"] == stats["failures"] == 1
    assert stats["response_seconds"] == pytest.approx(0.02)
    assert sum(waits) >= (60 if stats["last_failure_category"] == "throttle" else 1)
    assert "secret" not in str(execution.metrics())


@pytest.mark.parametrize(
    "failure, attempts", [(Timeout("secret"), 2), (ValueError("permission secret"), 1)]
)
def test_exhaustion_and_permission_never_leak_provider_text(
    failure: Exception,
    attempts: int,
) -> None:
    execution, _, _ = fake_execution()

    def call() -> pd.DataFrame:
        raise failure

    with pytest.raises(TushareSourceError) as raised:
        execution.request("opt_daily", call)
    assert "secret" not in str(raised.value)
    assert execution.metrics()["attempts"] == attempts


def test_parallel_network_requests_can_overlap() -> None:
    execution, _, _ = fake_execution()
    entered = Event()
    second = Event()

    def first() -> pd.DataFrame:
        entered.set()
        assert second.wait(2)
        return pd.DataFrame()

    def next_call() -> pd.DataFrame:
        second.set()
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(execution.request, "fut_daily", first)
        assert entered.wait(2)
        other = pool.submit(execution.request, "fut_daily", next_call)
        future.result()
        other.result()
    assert execution.metrics()["attempts"] == 2
