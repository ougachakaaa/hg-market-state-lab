"""Shared scheduling, credential lifecycle and provider error boundary."""

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


@pytest.mark.parametrize("rate", [200, 500])
def test_account_rate_shared_across_instances(monkeypatch: pytest.MonkeyPatch, rate: int) -> None:
    monkeypatch.setenv("TUSHARE_CALLS_PER_MINUTE", str(rate))
    clock = [100.0]
    starts: list[float] = []
    monkeypatch.setattr(_executor.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        _executor.time, "sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )

    class Client:
        def query(self, **params: object) -> object:
            starts.append(clock[0])
            return object()

    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    for _ in range(3):
        TushareExecutor().call("query")
    assert starts == pytest.approx([100, 100 + 60 / rate, 100 + 120 / rate])
