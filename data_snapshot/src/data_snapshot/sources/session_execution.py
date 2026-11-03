"""Budget and safe endpoint diagnostics for MO historical acquisition sessions."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

import pandas as pd
from requests.exceptions import ConnectionError, Timeout

from .tushare import TushareApi, TushareSourceError


@dataclass
class EndpointMetrics:
    attempts: int = 0
    response_seconds: float = 0.0
    pacing_seconds: float = 0.0
    retries: int = 0
    failures: int = 0
    last_failure_category: str | None = None


class RequestBudget:
    """Process-local start pacing; the network call never holds this lock."""

    def __init__(
        self,
        requests_per_minute: int = 450,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.interval = 60 / requests_per_minute
        self.clock = clock
        self.sleep = sleep
        self.lock = Lock()
        self.next_start = 0.0

    def reserve(self) -> float:
        started = self.clock()
        with self.lock:
            delay = max(0.0, self.next_start - self.clock())
            if delay:
                self.sleep(delay)
            self.next_start = self.clock() + self.interval
            return self.clock() - started

    def pause(self, seconds: float) -> None:
        with self.lock:
            self.next_start = max(self.next_start, self.clock() + seconds)


PROCESS_BUDGET = RequestBudget()


def failure_category(exc: Exception) -> str:
    if isinstance(exc, ConnectionError | Timeout):
        return "connection"
    message = str(exc).lower()
    if any(term in message for term in ("频率超限", "rate limit", "too many requests")):
        return "throttle"
    return "provider_rejected"


class SessionExecution:
    """One acquisition's metrics, sharing the process request-start budget."""

    def __init__(self, budget: RequestBudget | None = None) -> None:
        self.budget = PROCESS_BUDGET if budget is None else budget
        self.lock = Lock()
        self.endpoints: dict[str, EndpointMetrics] = {}

    def request(self, endpoint: str, call: Callable[[], pd.DataFrame]) -> pd.DataFrame:
        for attempt in range(2):
            waited = self.budget.reserve()
            with self.lock:
                metric = self.endpoints.setdefault(endpoint, EndpointMetrics())
                metric.attempts += 1
                metric.pacing_seconds += waited
                metric.retries += int(attempt > 0)
            start = self.budget.clock()
            try:
                return call()
            except Exception as exc:
                category = failure_category(exc)
                with self.lock:
                    metric.failures += 1
                    metric.last_failure_category = category
            finally:
                elapsed = self.budget.clock() - start
                with self.lock:
                    metric.response_seconds += elapsed
            if attempt == 0 and category in ("connection", "throttle"):
                if category == "throttle":
                    self.budget.pause(60)
                else:
                    self.budget.sleep(1)
                continue
            # Never expose provider text: it can contain proxy credentials or tokens.
            raise TushareSourceError(f"{endpoint}: {category} failure") from None
        raise AssertionError("unreachable")

    def metrics(self) -> dict[str, Any]:
        with self.lock:
            endpoints = {key: asdict(value) for key, value in sorted(self.endpoints.items())}
        return {
            "attempts": sum(value["attempts"] for value in endpoints.values()),
            "endpoints": endpoints,
        }

    def wrap(self, api: TushareApi) -> BudgetedApi:
        return BudgetedApi(api, self)


class BudgetedApi:
    """Only the five endpoint methods required by MO sessions are routed."""

    def __init__(self, api: TushareApi, execution: SessionExecution) -> None:
        self.api = api
        self.execution = execution

    def _query(self, endpoint: str, kwargs: dict[str, Any]) -> pd.DataFrame:
        return self.execution.request(endpoint, lambda: getattr(self.api, endpoint)(**kwargs))

    def index_daily(self, **kwargs: Any) -> pd.DataFrame:
        return self._query("index_daily", kwargs)

    def opt_basic(self, **kwargs: Any) -> pd.DataFrame:
        return self._query("opt_basic", kwargs)

    def opt_daily(self, **kwargs: Any) -> pd.DataFrame:
        return self._query("opt_daily", kwargs)

    def fut_basic(self, **kwargs: Any) -> pd.DataFrame:
        return self._query("fut_basic", kwargs)

    def fut_daily(self, **kwargs: Any) -> pd.DataFrame:
        return self._query("fut_daily", kwargs)
