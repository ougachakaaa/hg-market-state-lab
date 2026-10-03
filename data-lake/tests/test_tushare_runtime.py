"""Shared scheduling, credential lifecycle and provider error boundary."""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from data_lake import OperationError
from data_lake._domain import ExecutionFailure
from data_lake.providers.tushare import TushareExecutor, _executor


@pytest.fixture(autouse=True)
def isolated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_executor, "_states", {})
    monkeypatch.setenv("TUSHARE_TOKEN", "fake-token")


def test_shared_concurrent_starts_and_slow_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    starts: list[float] = []
    lock = threading.Lock()
    clients: list[str] = []
    response = object()

    class Client:
        def query(self, **params: Any) -> object:
            with params.pop("dispatch")():
                with lock:
                    starts.append(time.monotonic())
            time.sleep(0.6)
            return response

    def create(token: str) -> Client:
        clients.append(token)
        return Client()

    monkeypatch.setattr(_executor, "create_client", create)
    executors = [TushareExecutor() for _ in range(4)]
    assert clients == []
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda executor: executor.call("query", native="unchanged"), executors)
        )
    assert all(result is response for result in results)
    assert clients == ["fake-token"]
    assert all(right - left >= 1 / 3 for left, right in zip(starts, starts[1:], strict=False))
    assert starts[1] - starts[0] < 0.5  # starts are independent of completion
    TushareExecutor().call("query")
    assert clients == ["fake-token"]


def test_failure_counts_as_start_without_retry_or_secret_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    starts = []

    class Client:
        def query(self, **params: Any) -> object:
            with params.pop("dispatch")():
                starts.append(time.monotonic())
                raise RuntimeError("fake-token private SDK details")

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    for _ in range(2):
        with pytest.raises(ExecutionFailure) as caught:
            TushareExecutor().call("query")
        assert caught.value.code == "source_request"
        assert "fake-token" not in caught.value.reason
    assert len(starts) == 2 and starts[1] - starts[0] >= 1 / 3


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_credentials_never_create_client(
    monkeypatch: pytest.MonkeyPatch, token: str | None
) -> None:
    monkeypatch.setattr(_executor, "dotenv_values", lambda path: {})
    if token is None:
        monkeypatch.delenv("TUSHARE_TOKEN")
    else:
        monkeypatch.setenv("TUSHARE_TOKEN", token)
    monkeypatch.setattr(_executor, "create_client", lambda token: pytest.fail("no client expected"))
    executor = TushareExecutor()
    with pytest.raises(OperationError, match="credential"):
        executor.call("query")


def test_blank_environment_does_not_use_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", " ")
    monkeypatch.setattr(_executor, "dotenv_values", lambda path: pytest.fail("no fallback"))
    with pytest.raises(OperationError):
        TushareExecutor().prepare()


def test_fallback_path_and_initialization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN")
    paths = []

    def dotenv(path: Path) -> dict[str, str]:
        paths.append(path)
        return {"TUSHARE_TOKEN": "fallback"}

    monkeypatch.setattr(_executor, "dotenv_values", dotenv)

    def broken(token: str) -> object:
        raise RuntimeError("SDK initialization")

    monkeypatch.setattr(_executor, "create_client", broken)
    with pytest.raises(OperationError, match="initialized"):
        TushareExecutor().prepare()
    assert paths == [Path(__file__).resolve().parents[2] / "market-snapshot/.env"]


@pytest.mark.parametrize("rate", ["0", "501", "abc", "200.0"])
def test_invalid_rate_is_lazy_operation_failure(monkeypatch: pytest.MonkeyPatch, rate: str) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", rate)
    monkeypatch.setattr(_executor, "create_client", lambda token: pytest.fail("no client"))
    executor = TushareExecutor()
    with pytest.raises(OperationError, match="1..500"):
        executor.call("query")


@pytest.mark.parametrize("rate", [180, 200, 500])
def test_account_rate_shared_across_instances(monkeypatch: pytest.MonkeyPatch, rate: int) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", str(rate))
    clock = [100.0]
    starts: list[float] = []
    monkeypatch.setattr(_executor.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        _executor.time, "sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )

    class Client:
        def query(self, **params: Any) -> object:
            with params.pop("dispatch")():
                starts.append(clock[0])
            return object()

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    for _ in range(3):
        TushareExecutor().call("query")
    assert starts == pytest.approx([100, 100 + 60 / rate, 100 + 120 / rate])


def test_slow_logging_does_not_delay_an_already_reserved_send(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", "500")
    logging_entered = threading.Event()
    second_sent = threading.Event()
    starts: list[float] = []

    class Client:
        def query(self, **params: Any) -> object:
            with params.pop("dispatch")():
                starts.append(time.monotonic())
                if params["second"]:
                    second_sent.set()
            return object()

    class SlowHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.msg.startswith("request_start") and not logging_entered.is_set():
                logging_entered.set()
                assert second_sent.wait(3)

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    caplog.set_level(logging.DEBUG, logger="data_lake")
    monkeypatch.setattr(_executor.logger, "handlers", [SlowHandler()])
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(TushareExecutor().call, "query", second=False)
        assert logging_entered.wait(3)
        second = pool.submit(TushareExecutor().call, "query", second=True)
        first.result(timeout=3)
        second.result(timeout=3)
    assert len(starts) == 2 and starts[1] - starts[0] >= 0.12


def test_delay_before_sending_cannot_reorder_reserved_slots_into_a_burst(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", "500")
    prepared = threading.Event()
    second_sent = threading.Event()
    starts: list[tuple[bool, float]] = []

    class Client:
        def query(self, **params: Any) -> object:
            if not params["second"]:
                prepared.set()
                assert second_sent.wait(3)
            with params.pop("dispatch")():
                starts.append((params["second"], time.monotonic()))
                if params["second"]:
                    second_sent.set()
            return object()

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(TushareExecutor().call, "query", second=False)
        assert prepared.wait(3)
        pool.submit(TushareExecutor().call, "query", second=True).result(timeout=3)
        first.result(timeout=3)
    assert [second for second, _ in starts] == [True, False]
    assert starts[1][1] - starts[0][1] >= 0.12


@pytest.mark.parametrize("rate", [180, 200, 500])
def test_failed_prolonged_send_charged_until_exit_and_releases_gate(
    monkeypatch: pytest.MonkeyPatch, rate: int
) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", str(rate))
    clock = [100.0]
    starts: list[float] = []
    monkeypatch.setattr(_executor.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        _executor.time, "sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )

    class Client:
        def query(self, **params: Any) -> object:
            with params.pop("dispatch")():
                starts.append(clock[0])
                if len(starts) == 1:
                    clock[0] += 0.25
                    raise OSError("fake-token private failure")
            return object()

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    with pytest.raises(ExecutionFailure) as caught:
        TushareExecutor().call("query")
    assert "fake-token" not in caught.value.reason
    TushareExecutor().call("query")
    assert starts == pytest.approx([100, 100.25 + 60 / rate])


def test_cancel_guard_allows_inflight_call_to_finish_but_stops_subsequent_pages() -> None:
    started = threading.Event()
    release = threading.Event()
    calls: list[str] = []
    response = object()

    class Delegate:
        def call(self, endpoint: str, **parameters: Any) -> object:
            calls.append(endpoint)
            started.set()
            assert release.wait(3)
            return response

    guarded = _executor.CancellableExecutor(Delegate())
    with ThreadPoolExecutor(max_workers=1) as worker:
        future = worker.submit(guarded.call, "opt_daily", offset=0)
        assert started.wait(3)
        guarded.cancel()
        release.set()
        assert future.result() is response
    with pytest.raises(ExecutionFailure, match="cancelled"):
        guarded.call("opt_daily", offset=4000)
    assert calls == ["opt_daily"]
