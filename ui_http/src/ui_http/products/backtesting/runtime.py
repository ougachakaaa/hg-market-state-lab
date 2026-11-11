"""One online application per process, without I/O during schema construction."""

from threading import Lock

from fastapi import FastAPI

from market_backtesting.cases.futures_roll_long import (
    FuturesRollOnlineApplication,
    FuturesRollOnlineError,
    create_futures_roll_online_application,
)


class OnlineRuntime:
    def __init__(self) -> None:
        self.lock = Lock()
        self.initialized = False
        self.application: FuturesRollOnlineApplication | None = None

    def get(self) -> FuturesRollOnlineApplication:
        with self.lock:
            if not self.initialized:
                try:
                    # Keep the facade even if its Store failed: preflight still works.
                    self.application = create_futures_roll_online_application()
                except Exception:
                    self.application = None
                self.initialized = True
            if self.application is None:
                raise FuturesRollOnlineError("unavailable")
            return self.application


_runtime = OnlineRuntime()


def application(app: FastAPI) -> FuturesRollOnlineApplication:
    injected: FuturesRollOnlineApplication | None = getattr(
        app.state, "backtesting_application", None
    )
    return injected if injected is not None else _runtime.get()


def initialize(app: FastAPI) -> None:
    try:
        application(app)
    except FuturesRollOnlineError:
        pass
