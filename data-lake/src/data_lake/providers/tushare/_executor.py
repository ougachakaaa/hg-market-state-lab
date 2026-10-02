"""Lazy credential-local client and process-local request-start schedule."""

import os
import threading
import time
from pathlib import Path
from typing import Any, Protocol

from dotenv import dotenv_values

from data_lake._domain import ExecutionFailure
from data_lake.results import OperationError

_states: dict[str, "_State"] = {}
_states_lock = threading.Lock()


class Executor(Protocol):
    def call(self, endpoint: str, **parameters: Any) -> Any: ...


def resolve_credential() -> str:
    token = os.environ.get("TUSHARE_TOKEN")
    if token is None:
        root = Path(__file__).resolve().parents[5]
        token = dotenv_values(root / "market-snapshot/.env").get("TUSHARE_TOKEN")
    if not token or not token.strip():
        raise OperationError("TUSHARE_TOKEN credential is required for Source I/O")
    return token


class _State:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.lock = threading.Lock()
        self.last_start = float("-inf")

    def start(self) -> None:
        with self.lock:
            while (delay := self.last_start + 0.12 - time.monotonic()) > 0:
                time.sleep(delay)
            self.last_start = time.monotonic()


class TushareExecutor:
    def prepare(self) -> "TushareExecutor":
        self._state()
        return self

    def _state(self) -> _State:
        try:
            token = resolve_credential()
            with _states_lock:
                if token not in _states:
                    import tushare

                    _states[token] = _State(tushare.pro_api(token))
                return _states[token]
        except OperationError:
            raise
        except Exception as exc:
            raise OperationError("Tushare Source could not be initialized") from exc

    def call(self, endpoint: str, **parameters: object) -> Any:
        state = self._state()
        state.start()
        try:
            return getattr(state.client, endpoint)(**parameters)
        except Exception as exc:
            # SDK messages may contain credentials; publish only a safe reason.
            raise ExecutionFailure("Tushare provider request failed", "source_request") from exc
