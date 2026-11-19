"""Single process application lifetime; offline schema construction performs no I/O."""

import logging
from os import getpid
from threading import Lock
from time import monotonic

from fastapi import FastAPI

from market_research.descriptive.cases.futures_basis import (
    ACTIVE_RUN_VERSION,
    FuturesBasisOnlineApplication,
    OnlineError,
    OnlineInitializationError,
)

_LOG = logging.getLogger("uvicorn.error.futures_basis")
_RETRY_DELAY_SECONDS = 30
_MAX_ATTEMPTS = 3


class OnlineRuntime:
    def __init__(self) -> None:
        self.lock = Lock()
        self.attempts = 0
        self.retry_at: float | None = None
        self.application: FuturesBasisOnlineApplication | None = None

    def get(self, operation: str = "read") -> FuturesBasisOnlineApplication:
        with self.lock:
            if self.application is not None:
                return self.application
            initial = self.attempts == 0 and operation in {"startup", "submit"}
            retry = (
                operation == "submit" and self.retry_at is not None and monotonic() >= self.retry_at
            )
            if not (initial or retry):
                raise OnlineError("unavailable")
            self.attempts += 1
            self.retry_at = None
            try:
                self.application = FuturesBasisOnlineApplication()
            except Exception as exc:
                stage, category, exception_type, sqlite_code = (
                    "application",
                    "unexpected",
                    type(exc).__name__,
                    None,
                )
                if isinstance(exc, OnlineInitializationError):
                    stage = exc.stage
                    category = exc.category
                    exception_type = exc.exception_type
                    sqlite_code = exc.sqlite_code
                    if exc.retryable and self.attempts < _MAX_ATTEMPTS:
                        self.retry_at = monotonic() + _RETRY_DELAY_SECONDS
                action = (
                    "retry_explicit_submit_after_30s"
                    if self.retry_at is not None
                    else "inspect_storage_and_restart_backend"
                )
                _LOG.error(
                    "futures_basis_initialization_failed pid=%s attempt=%s operation=%s "
                    "active_run_version=%s stage=%s category=%s exception_type=%s "
                    "sqlite_code=%s action=%s",
                    getpid(),
                    self.attempts,
                    operation,
                    ACTIVE_RUN_VERSION,
                    stage,
                    category,
                    exception_type,
                    sqlite_code,
                    action,
                )
                raise OnlineError("unavailable") from None
            _LOG.info(
                "futures_basis_initialization_succeeded pid=%s attempt=%s operation=%s "
                "active_run_version=%s",
                getpid(),
                self.attempts,
                operation,
                ACTIVE_RUN_VERSION,
            )
            return self.application


_runtime = OnlineRuntime()


def application(app: FastAPI, operation: str = "read") -> FuturesBasisOnlineApplication:
    injected: FuturesBasisOnlineApplication | None = getattr(
        app.state, "futures_basis_application", None
    )
    return injected if injected is not None else _runtime.get(operation)


def initialize(app: FastAPI) -> None:
    try:
        application(app, "startup")
    except OnlineError:
        pass
