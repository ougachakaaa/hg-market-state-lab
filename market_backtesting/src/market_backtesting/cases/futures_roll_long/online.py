"""Single-process online composition of the accepted WP3/WP4 execution path."""

import hashlib
import threading
from pathlib import Path
from typing import Protocol

from lab_config import ConfigError, backtesting_run_root

from .application import create_futures_roll_service
from .application_models import (
    FuturesRollExecution,
    FuturesRollReadiness,
    FuturesRollRequest,
    validate_futures_roll_request,
)
from .failures import FuturesRollError
from .online_codec import RESULT_LIMIT, decode_result, encode_result
from .online_models import (
    FuturesRollOnlineError,
    OnlineFailure,
    OnlineRunStatus,
    project_failure,
)
from .online_store import FuturesRollRunStore, read_bytes, supports_storage, valid_id
from .result import build_backtest_result
from .result_models import BacktestResult
from .result_validation import validate_backtest_result

# W2 guards are independent of every other product. Lock only short state operations.
_PROCESS_LOCK = threading.RLock()
_RUN_GUARD = threading.Lock()
_ACTIVE: tuple[str, str] | None = None
_READ_PERMIT = threading.BoundedSemaphore(1)


class OnlineService(Protocol):
    def run(self, request: FuturesRollRequest) -> FuturesRollExecution: ...
    def preflight(self, request: FuturesRollRequest) -> FuturesRollReadiness: ...


def _owner(owner_scope: str) -> None:
    if type(owner_scope) is not str or not owner_scope:
        raise FuturesRollOnlineError("invalid_request")


class FuturesRollOnlineApplication:
    """Facade for WP6; store failure does not disable read-only preflight."""

    def __init__(self, *, root: Path | None = None, service: OnlineService | None = None) -> None:
        self._service = service if service is not None else create_futures_roll_service()
        self._store: FuturesRollRunStore | None = None
        self._unavailable: str | None = None
        with _PROCESS_LOCK:
            try:
                if not supports_storage():
                    raise FuturesRollOnlineError("unavailable")
                configured = backtesting_run_root() if root is None else None
                selected = (
                    Path(configured)
                    if configured is not None
                    else root
                    if root is not None
                    else Path(__file__).resolve().parents[4]
                    / ".runtime"
                    / "futures_roll_long_online"
                )
                self._store = FuturesRollRunStore(selected)
                self._store.recover(_ACTIVE)
            except FuturesRollOnlineError as exc:
                self._unavailable = exc.category
            except (OSError, ConfigError, ValueError, TypeError, RecursionError, FuturesRollError):
                self._unavailable = "unavailable"

    def _available(self) -> FuturesRollRunStore:
        if self._unavailable is not None or self._store is None:
            raise FuturesRollOnlineError(self._unavailable or "unavailable")
        return self._store

    def preflight(self, request: FuturesRollRequest, owner_scope: str) -> FuturesRollReadiness:
        _owner(owner_scope)
        validate_futures_roll_request(request)
        return self._service.preflight(request)

    def submit(self, request: FuturesRollRequest, owner_scope: str) -> OnlineRunStatus:
        global _ACTIVE
        _owner(owner_scope)
        validate_futures_roll_request(request)
        if not _RUN_GUARD.acquire(blocking=False):
            raise FuturesRollOnlineError("run_busy")
        handed_off = False
        try:
            with _PROCESS_LOCK:
                store = self._available()
                try:
                    accepted = store.create(request, owner_scope)
                except (OSError, ValueError, TypeError, RecursionError):
                    self._unavailable = "unavailable"
                    raise FuturesRollOnlineError("unavailable") from None
                _ACTIVE = (str(store.root), accepted.run_id)
                try:
                    threading.Thread(
                        target=self._execute,
                        args=(accepted.run_id, request),
                        name="w2-backtest-worker",
                        daemon=True,
                    ).start()
                except BaseException:
                    try:
                        store.transition(
                            accepted.run_id,
                            "FAILED",
                            failure=project_failure(RuntimeError(), "execution"),
                        )
                    except BaseException:
                        self._unavailable = "unavailable"
                    finally:
                        _ACTIVE = None
                else:
                    handed_off = True
                return accepted
        finally:
            if not handed_off:
                _RUN_GUARD.release()

    def _execute(self, run_id: str, request: FuturesRollRequest) -> None:
        global _ACTIVE
        stage = "execution"
        try:
            with _PROCESS_LOCK:
                store = self._available()
                store.transition(run_id, "RUNNING")
            # WP3 classifies actual prepare/replay/analysis operations itself.
            stage = "prepare"
            execution = self._service.run(request)
            stage = "result_validation"
            result = build_backtest_result(execution)
            validate_backtest_result(result, execution)
            stage = "result_publication"
            try:
                payload = encode_result(result, request)
            except FuturesRollOnlineError:
                raise
            except (ValueError, TypeError, OverflowError, RecursionError):
                raise FuturesRollOnlineError("serialization_failure") from None
            store.publish(run_id, payload)
        except BaseException as exc:
            if stage == "result_publication" and isinstance(exc, OSError | FuturesRollOnlineError):
                category = (
                    exc.category
                    if isinstance(exc, FuturesRollOnlineError)
                    and exc.category in {"result_too_large", "serialization_failure"}
                    else "storage_failure"
                )
                failure = OnlineFailure(stage, category, None, category)
            else:
                failure = project_failure(exc, stage)
            with _PROCESS_LOCK:
                try:
                    self._available().transition(run_id, "FAILED", failure=failure)
                except BaseException:
                    self._unavailable = "unavailable"
        finally:
            with _PROCESS_LOCK:
                _ACTIVE = None
                _RUN_GUARD.release()

    def get_status(self, run_id: str, owner_scope: str) -> OnlineRunStatus:
        valid_id(run_id)
        _owner(owner_scope)
        try:
            with _PROCESS_LOCK:
                store = self._available()
                status = store.status(run_id, owner_scope)
                if status.status in {"PENDING", "RUNNING"} and _ACTIVE != (str(store.root), run_id):
                    raise FuturesRollOnlineError("unavailable")
                return status
        except (OSError, ValueError, TypeError, RecursionError, FuturesRollError):
            raise FuturesRollOnlineError("corrupt") from None

    def get_result(self, run_id: str, owner_scope: str) -> BacktestResult:
        valid_id(run_id)
        _owner(owner_scope)
        try:
            # Authorize before permit acquisition so busy never reveals foreign records.
            with _PROCESS_LOCK:
                store = self._available()
                status = store.status(run_id, owner_scope)
                if status.status != "COMPLETED":
                    raise FuturesRollOnlineError("result_not_ready")
            if not _READ_PERMIT.acquire(blocking=False):
                raise FuturesRollOnlineError("read_busy")
            try:
                with store.directory(run_id) as fd:
                    _, state, request = store.record(fd, run_id, owner_scope)
                    if state["status"] != "COMPLETED":
                        raise FuturesRollOnlineError("corrupt")
                    payload = read_bytes(fd, "result.json", RESULT_LIMIT)
                if hashlib.sha256(payload).hexdigest() != state["result_digest"]:
                    raise FuturesRollOnlineError("corrupt")
                return decode_result(payload, request)
            finally:
                _READ_PERMIT.release()
        except (OSError, ValueError, TypeError, OverflowError, RecursionError, FuturesRollError):
            raise FuturesRollOnlineError("corrupt") from None


def create_futures_roll_online_application(
    *,
    root: Path | None = None,
    service: OnlineService | None = None,
) -> FuturesRollOnlineApplication:
    return FuturesRollOnlineApplication(root=root, service=service)
