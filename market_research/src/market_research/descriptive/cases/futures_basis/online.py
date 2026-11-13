"""Case-specific online application and bounded, private run store."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lab_config import ConfigError, futures_basis_run_root

from .evidence import encode, scientific_payload
from .inputs import FuturesBasisRequest, InputPreparationError
from .observations import ObservationConstructionError
from .online_record import (
    MAX_REPORT_BYTES,
    OnlineError,
    _ExecutionFailure,
    _failure,
    _validate_reader,
    standard_report_request,
)
from .online_record import (
    PROFILE as PROFILE,
)
from .online_sqlite_store import FuturesBasisSQLiteRunStore
from .report import ReportResult, compose_report
from .service import observe_futures_basis

_PROCESS_LOCK = threading.RLock()
_PROCESS_ACTIVE: tuple[str, str] | None = None
_UNAVAILABLE: set[str] = set()
_READ_PERMIT = threading.BoundedSemaphore(1)


@dataclass(frozen=True)
class OnlineServices:
    calendar: Any = None
    futures: Any = None
    index: Any = None


class FuturesBasisOnlineApplication:
    """One active run, persisted state and read-only historical projection."""

    def __init__(
        self,
        *,
        root: Path | None = None,
        services: OnlineServices | None = None,
        observe: Callable[..., Any] = observe_futures_basis,
        compose: Callable[..., ReportResult] = compose_report,
    ) -> None:
        try:
            configured = futures_basis_run_root() if root is None else None
        except ConfigError:
            raise OnlineError("unavailable") from None
        self.root = (
            Path(configured)
            if configured is not None
            else root or Path(__file__).resolve().parents[5] / ".runtime" / "futures_basis_online"
        )
        self.services = services or OnlineServices()
        self.observe = observe
        self.compose = compose
        self._store = FuturesBasisSQLiteRunStore(self.root)
        with _PROCESS_LOCK:
            self._available()
            self._store.recover(_PROCESS_ACTIVE)

    def _available(self) -> None:
        if str(self.root) in _UNAVAILABLE:
            raise OnlineError("unavailable")

    def submit(self, request: FuturesBasisRequest, owner_scope: str) -> dict[str, Any]:
        global _PROCESS_ACTIVE
        try:
            standard_report_request(request)
        except (ValueError, TypeError):
            raise OnlineError("invalid_request") from None
        if type(owner_scope) is not str or not owner_scope:
            raise OnlineError("invalid_request")
        with _PROCESS_LOCK:
            self._available()
            if _PROCESS_ACTIVE is not None:
                raise OnlineError("run_busy")
            accepted = self._store.create(request, owner_scope)
            run_id = accepted["run_id"]
            _PROCESS_ACTIVE = (str(self.root), run_id)
            try:
                threading.Thread(target=self._execute, args=(run_id, request), daemon=True).start()
            except BaseException as exc:
                try:
                    self._store.transition(run_id, "FAILED", _failure(exc))
                except BaseException:
                    _UNAVAILABLE.add(str(self.root))
                finally:
                    _PROCESS_ACTIVE = None
                raise OnlineError("unavailable") from None
            return accepted

    def _execute(self, run_id: str, request: FuturesBasisRequest) -> None:
        global _PROCESS_ACTIVE
        try:
            self._store.transition(run_id, "RUNNING")
            try:
                source = self.observe(
                    request,
                    calendar_service=self.services.calendar,
                    futures_service=self.services.futures,
                    index_service=self.services.index,
                )
            except InputPreparationError as exc:
                raise _ExecutionFailure("input_preparation", exc.category, exc.dependency) from None
            except ObservationConstructionError as exc:
                raise _ExecutionFailure("observation_construction", exc.category) from None
            try:
                report = self.compose(source, standard_report_request(request))
            except (ValueError, TypeError):
                raise _ExecutionFailure("report_composition", "invalid_report_request") from None
            except Exception:
                raise _ExecutionFailure("report_composition", "composition_failure") from None
            try:
                reader = scientific_payload(report)[3]
                _validate_reader(reader, report, request)
                buffer = bytearray()
                encoder = json.JSONEncoder(
                    ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
                )
                for chunk in encoder.iterencode(encode(reader)):
                    encoded = chunk.encode("utf-8")
                    if len(buffer) + len(encoded) > MAX_REPORT_BYTES:
                        raise _ExecutionFailure("result_publication", "result_too_large")
                    buffer.extend(encoded)
                payload = bytes(buffer)
            except _ExecutionFailure:
                raise
            except Exception:
                raise _ExecutionFailure("result_publication", "serialization_failure") from None
            if len(payload) > MAX_REPORT_BYTES:
                raise _ExecutionFailure("result_publication", "result_too_large")
            with _PROCESS_LOCK:
                self._store.publish(run_id, payload, report.status)
                _PROCESS_ACTIVE = None
        except BaseException as exc:
            with _PROCESS_LOCK:
                try:
                    self._store.transition(run_id, "FAILED", _failure(exc))
                except BaseException:
                    _UNAVAILABLE.add(str(self.root))
                finally:
                    _PROCESS_ACTIVE = None

    def get_run(self, run_id: str, owner_scope: str) -> dict[str, Any]:
        self._store.valid_id(run_id)
        with _PROCESS_LOCK:
            self._available()
            result = self._store.status(run_id, owner_scope)
            if result["status"] in {"PENDING", "RUNNING"} and _PROCESS_ACTIVE != (
                str(self.root),
                run_id,
            ):
                raise OnlineError("unavailable")
            return result

    def get_report(self, run_id: str, owner_scope: str) -> dict[str, Any]:
        self._store.valid_id(run_id)
        with _PROCESS_LOCK:
            self._available()
            # Owner authorization precedes the full-reader permit, even under contention.
            self._store.authorize(run_id, owner_scope)
        if not _READ_PERMIT.acquire(blocking=False):
            raise OnlineError("read_busy")
        try:
            return self._store.read_report(run_id, owner_scope)
        finally:
            _READ_PERMIT.release()
