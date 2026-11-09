"""Single process application lifetime; offline schema construction performs no I/O."""

from threading import Lock

from fastapi import FastAPI

from market_research.descriptive.cases.futures_basis import (
    FuturesBasisOnlineApplication,
    OnlineError,
)


class OnlineRuntime:
    def __init__(self) -> None:
        self.lock = Lock()
        self.initialized = False
        self.application: FuturesBasisOnlineApplication | None = None

    def get(self) -> FuturesBasisOnlineApplication:
        with self.lock:
            if not self.initialized:
                try:
                    self.application = FuturesBasisOnlineApplication()
                except Exception:
                    # Initialization cannot compromise sibling products or expose diagnostics.
                    self.application = None
                self.initialized = True
            if self.application is None:
                raise OnlineError("unavailable")
            return self.application


_runtime = OnlineRuntime()


def application(app: FastAPI) -> FuturesBasisOnlineApplication:
    injected: FuturesBasisOnlineApplication | None = getattr(
        app.state, "futures_basis_application", None
    )
    return injected if injected is not None else _runtime.get()


def initialize(app: FastAPI) -> None:
    try:
        application(app)
    except OnlineError:
        pass
