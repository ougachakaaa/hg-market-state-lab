"""Shared scheduling, credential lifecycle and provider error boundary."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
import tushare

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
            time.sleep(0.4)
            return response

    def create(token: str) -> Client:
        clients.append(token)
        return Client()

    monkeypatch.setattr(tushare, "pro_api", create)
    executors = [TushareExecutor() for _ in range(4)]
    assert clients == []
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda executor: executor.call("query", native="unchanged"), executors)
        )
    assert all(result is response for result in results)
    assert clients == ["fake-token"]
    assert all(right - left >= 0.12 for left, right in zip(starts, starts[1:], strict=False))
    assert starts[1] - starts[0] < 0.3  # starts are independent of completion
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

    monkeypatch.setattr(tushare, "pro_api", lambda token: Client())
    for _ in range(2):
        with pytest.raises(ExecutionFailure) as caught:
            TushareExecutor().call("query")
        assert caught.value.code == "source_request"
        assert "fake-token" not in caught.value.reason
    assert len(starts) == 2 and starts[1] - starts[0] >= 0.12


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_credentials_never_create_client(
    monkeypatch: pytest.MonkeyPatch, token: str | None
) -> None:
    monkeypatch.setattr(_executor, "dotenv_values", lambda path: {})
    if token is None:
        monkeypatch.delenv("TUSHARE_TOKEN")
    else:
        monkeypatch.setenv("TUSHARE_TOKEN", token)
    monkeypatch.setattr(tushare, "pro_api", lambda token: pytest.fail("no client expected"))
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

    monkeypatch.setattr(tushare, "pro_api", broken)
    with pytest.raises(OperationError, match="initialized"):
        TushareExecutor().prepare()
    assert paths == [Path(__file__).resolve().parents[2] / "market-snapshot/.env"]
