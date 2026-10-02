"""Lazy credential-local client and process-local request-start schedule."""

import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Protocol

from dotenv import dotenv_values

from data_lake._domain import ExecutionFailure
from data_lake.results import OperationError

from ._client import Client as create_client
from ._client import RequestFailure

logger = logging.getLogger(__name__)
SELECTORS = {
    "ts_code",
    "exchange",
    "market",
    "trade_date",
    "start_date",
    "end_date",
    "offset",
    "limit",
    "fut_type",
}


def request_interval() -> float:
    try:
        rate = int(os.environ.get("TUSHARE_CALLS_PER_MINUTE", "180"))
        if not 1 <= rate <= 500:
            raise ValueError
    except ValueError:
        raise OperationError("TUSHARE_CALLS_PER_MINUTE must be an integer in 1..500") from None
    return 60 / rate


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
    def __init__(self, client: Any, interval: float, secret: str) -> None:
        self.client = client
        self.lock = threading.Lock()
        self.last_start = float("-inf")
        self.interval = interval
        self.secret = secret

    def start(self) -> float:
        entered = time.monotonic()
        with self.lock:
            while (delay := self.last_start + self.interval - time.monotonic()) > 0:
                time.sleep(delay)
            self.last_start = time.monotonic()
            return self.last_start - entered


class TushareExecutor:
    def prepare(self) -> "TushareExecutor":
        self._state()
        return self

    def _state(self) -> _State:
        try:
            token = resolve_credential()
            interval = request_interval()
            with _states_lock:
                if token not in _states:
                    _states[token] = _State(create_client(token), interval, token)
                elif _states[token].interval != interval:
                    raise OperationError("Tushare rate configuration changed within this process")
                return _states[token]
        except OperationError:
            raise
        except Exception as exc:
            raise OperationError("Tushare Source could not be initialized") from exc

    def call(self, endpoint: str, **parameters: object) -> Any:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", endpoint):
            raise OperationError("Invalid Tushare endpoint identifier")
        state = self._state()
        waited = state.start()
        started = time.monotonic()
        selectors = {
            key: value.replace(state.secret, "[redacted]") if isinstance(value, str) else value
            for key, value in parameters.items()
            if key in SELECTORS and isinstance(value, str | int) and not isinstance(value, bool)
        }
        logger.debug(
            "request_start endpoint=%s selectors=%s waited_seconds=%.3f",
            endpoint,
            selectors,
            waited,
        )
        try:
            response = getattr(state.client, endpoint)(**parameters)
        except RequestFailure as exc:
            suffix = f" code={exc.code}" if exc.code is not None else ""
            reason = f"Tushare {endpoint} request failed: {exc.kind}{suffix}"
            logger.warning(
                "request_failed endpoint=%s kind=%s code=%s elapsed_seconds=%.3f",
                endpoint,
                exc.kind,
                exc.code,
                time.monotonic() - started,
            )
            raise ExecutionFailure(reason, "source_request") from None
        except Exception:
            # SDK messages may contain credentials; publish only a safe reason.
            logger.warning(
                "request_failed endpoint=%s kind=unknown elapsed_seconds=%.3f",
                endpoint,
                time.monotonic() - started,
            )
            raise ExecutionFailure(
                f"Tushare {endpoint} request failed: unknown", "source_request"
            ) from None
        logger.debug(
            "request_complete endpoint=%s rows=%s elapsed_seconds=%.3f",
            endpoint,
            len(response) if hasattr(response, "__len__") else "unknown",
            time.monotonic() - started,
        )
        return response
