"""Case-specific online application and bounded, private run store."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from lab_config import ConfigError, futures_basis_run_root
from market_statistics import IntervalCountSpec, QuantileSpec

from .evidence import PROFILE_REPORT, json_bytes, scientific_payload
from .inputs import DEFINITION_VERSION, FuturesBasisRequest, InputPreparationError
from .observations import ObservationConstructionError
from .report import ReportRequest, ReportResult, compose_report
from .service import observe_futures_basis
from .validation import validate_online_request, validate_request

PROFILE = "r01a_standard_v1"
MAX_REPORT_BYTES = 32 * 1024 * 1024
ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
FAILURE_CATEGORIES = {
    "input_preparation": {"invalid_request", "upstream_operation", "invalid_public_input"},
    "observation_construction": {"invalid_prepared_inputs", "slot_resolution", "numerical_failure"},
    "report_composition": {"invalid_report_request", "composition_failure"},
    "result_publication": {"result_too_large", "serialization_failure"},
    "execution": {"interrupted", "internal_failure"},
}
DEPENDENCIES = {"request", "calendar_cffex", "calendar_sse", "futures", "index"}
_PROCESS_LOCK = threading.Lock()
_PROCESS_ACTIVE = False
_READ_PERMIT = threading.BoundedSemaphore(1)


class OnlineError(Exception):
    """Safe public application error; kind is mapped by the inbound adapter."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def standard_report_request(request: FuturesBasisRequest) -> ReportRequest:
    """Construct the frozen server-selected R01-A analysis profile."""
    validate_online_request(request)
    result = ReportRequest(
        request,
        QuantileSpec((0.0, 0.25, 0.5, 0.75, 1.0)),
        (
            IntervalCountSpec((-1000, -500, -100, 0, 100, 500, 1000), "index_points"),
            IntervalCountSpec((-1, -0.1, -0.01, 0, 0.01, 0.1, 1), "decimal_ratio"),
            IntervalCountSpec((-10, -1, -0.1, 0, 0.1, 1, 10), "decimal_ratio"),
        ),
    )
    result.validate()
    return result


def _request_data(request: FuturesBasisRequest) -> dict[str, str]:
    return dict(
        case=request.case,
        product_code=request.product_code,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat(),
        analysis_profile=PROFILE,
    )


def _validate_reader(reader: Any, report: ReportResult, request: FuturesBasisRequest) -> None:
    if not isinstance(reader, dict) or reader.get("profile") != PROFILE_REPORT:
        raise ValueError("Invalid reader profile")
    if report.status not in ("complete", "partial") or reader.get("status") != report.status:
        raise ValueError("Invalid report status")
    if report.request != standard_report_request(request):
        raise ValueError("Report request differs from standard profile")
    if reader.get("request") != json.loads(json_bytes(report.request)):
        raise ValueError("Reader request mismatch")
    if report.source.prepared.request != request:
        raise ValueError("Report source mismatch")
    fingerprint = report.source.prepared.input_fingerprint
    if (
        not isinstance(fingerprint, str)
        or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or reader.get("fingerprint") != fingerprint
        or reader.get("definition_version") != DEFINITION_VERSION
    ):
        raise ValueError("Invalid input fingerprint or definition")


def _supports_storage() -> bool:
    return (
        all(hasattr(os, name) for name in ("getuid", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
        and all(operation in os.supports_dir_fd for operation in (os.open, os.mkdir, os.unlink))
        and os.rename in os.supports_dir_fd
        and os.listdir in os.supports_fd
    )


def _safe_root(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise OnlineError("unavailable")
    current = Path(path.anchor)
    try:
        for part in path.parts[1:]:
            current = current / part
            if current.exists() or current.is_symlink():
                info = current.lstat()
                if not stat.S_ISDIR(info.st_mode):
                    raise OnlineError("unavailable")
            else:
                current.mkdir(mode=0o700)
        info = path.stat(follow_symlinks=False)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise OnlineError("unavailable")
        return path
    except OSError:
        raise OnlineError("unavailable") from None


def _open_dir(path: Path) -> int:
    # Recheck every ancestor at use time; openat operations stay attached to this inode.
    current = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = next_fd
        return current
    except OSError:
        os.close(current)
        raise OnlineError("unavailable") from None


def _decode(data: bytes) -> Any:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> Any:
        raise ValueError("Nonfinite JSON number")

    return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def _read(fd: int, name: str, limit: int) -> Any:
    try:
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                raise OnlineError("corrupt")
            data = os.read(file_fd, limit + 1)
            if len(data) > limit or os.read(file_fd, 1):
                raise OnlineError("corrupt")
        finally:
            os.close(file_fd)
        return _decode(data)
    except (OSError, ValueError, UnicodeError):
        raise OnlineError("corrupt") from None


def _write(fd: int, name: str, data: bytes) -> None:
    temporary = "." + secrets.token_hex(16)
    try:
        file_fd = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
        )
        try:
            with os.fdopen(file_fd, "wb", closefd=False) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(file_fd)
        finally:
            os.close(file_fd)
        os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    except OSError:
        raise OnlineError("unavailable") from None
    finally:
        try:
            os.unlink(temporary, dir_fd=fd)
        except FileNotFoundError:
            pass


def _state(
    status: str,
    created: str,
    started: str | None = None,
    finished: str | None = None,
    result_status: str | None = None,
    digest: str | None = None,
    failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return dict(
        version=1,
        status=status,
        created_at=created,
        started_at=started,
        finished_at=finished,
        result_status=result_status,
        result_digest=digest,
        failure=failure,
    )


def _valid_failure(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"stage", "category", "dependency", "reason"}:
        return False
    stage = value["stage"]
    if (
        type(stage) is not str
        or stage not in FAILURE_CATEGORIES
        or type(value["category"]) is not str
        or value["category"] not in FAILURE_CATEGORIES[stage]
    ):
        return False
    if stage == "input_preparation":
        if type(value["dependency"]) is not str or value["dependency"] not in DEPENDENCIES:
            return False
    elif value["dependency"] is not None:
        return False
    return value["reason"] == _failure_reason(stage, value["category"])


def _failure_reason(stage: str, category: str) -> str:
    if category == "interrupted":
        return "The previous execution was interrupted."
    return {
        "input_preparation": "Required public market inputs could not be prepared.",
        "observation_construction": "The observation could not be constructed.",
        "report_composition": "The report could not be composed.",
        "result_publication": "The report could not be published.",
        "execution": "The execution could not finish.",
    }[stage]


def _validate_state(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "version",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "result_status",
        "result_digest",
        "failure",
    }:
        raise OnlineError("corrupt")
    if type(value["version"]) is not int or value["version"] != 1:
        raise OnlineError("unsupported_version")
    status = value["status"]
    if status not in ("PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"):
        raise OnlineError("corrupt")
    if not isinstance(value["created_at"], str) or not value["created_at"]:
        raise OnlineError("corrupt")
    for key in ("started_at", "finished_at"):
        if value[key] is not None and not isinstance(value[key], str):
            raise OnlineError("corrupt")
    for key in ("created_at", "started_at", "finished_at"):
        if value[key] is not None:
            try:
                parsed = datetime.fromisoformat(value[key])
                offset = parsed.utcoffset()
                if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
                    raise ValueError
            except (ValueError, TypeError, AttributeError):
                raise OnlineError("corrupt") from None
    if status == "PENDING" and value["started_at"] is not None:
        raise OnlineError("corrupt")
    if status in ("RUNNING", "COMPLETED") and value["started_at"] is None:
        raise OnlineError("corrupt")
    if (value["finished_at"] is None) != (status in ("PENDING", "RUNNING")):
        raise OnlineError("corrupt")
    if status == "COMPLETED":
        if (
            value["result_status"] not in ("complete", "partial")
            or not isinstance(value["result_digest"], str)
            or re.fullmatch(r"[0-9a-f]{64}", value["result_digest"]) is None
            or value["failure"] is not None
        ):
            raise OnlineError("corrupt")
    elif (
        value["result_status"] is not None
        or value["result_digest"] is not None
        or (status in ("FAILED", "INTERRUPTED")) != (value["failure"] is not None)
    ):
        raise OnlineError("corrupt")
    if value["failure"] is not None and not _valid_failure(value["failure"]):
        raise OnlineError("corrupt")


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
        if not _supports_storage():
            raise OnlineError("unavailable")
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
        self._recover()

    def _directory(self, run_id: str) -> int:
        if type(run_id) is not str or ID_PATTERN.fullmatch(run_id) is None:
            raise OnlineError("run_not_found")
        root_fd = _open_dir(self.root)
        try:
            return os.open(run_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        except FileNotFoundError:
            raise OnlineError("run_not_found") from None
        except OSError:
            raise OnlineError("corrupt") from None
        finally:
            os.close(root_fd)

    def _recover(self) -> None:
        _safe_root(self.root)
        root_fd = _open_dir(self.root)
        try:
            for name in os.listdir(root_fd):
                if ID_PATTERN.fullmatch(name) is None:
                    continue
                fd = self._directory(name)
                try:
                    value = _read(fd, "state.json", 8192)
                    _validate_state(value)
                    if value["status"] in ("PENDING", "RUNNING"):
                        failure = dict(
                            stage="execution",
                            category="interrupted",
                            dependency=None,
                            reason=_failure_reason("execution", "interrupted"),
                        )
                        value = _state(
                            "INTERRUPTED",
                            value["created_at"],
                            value["started_at"],
                            _now(),
                            failure=failure,
                        )
                        _write(fd, "state.json", json_bytes(value))
                finally:
                    os.close(fd)
        finally:
            os.close(root_fd)

    def submit(self, request: FuturesBasisRequest, owner_scope: str) -> dict[str, Any]:
        global _PROCESS_ACTIVE
        try:
            standard_report_request(request)
        except (ValueError, TypeError):
            raise OnlineError("invalid_request") from None
        if type(owner_scope) is not str or not owner_scope:
            raise OnlineError("invalid_request")
        with _PROCESS_LOCK:
            if _PROCESS_ACTIVE:
                raise OnlineError("run_busy")
            _PROCESS_ACTIVE = True
            try:
                root_fd = _open_dir(self.root)
                try:
                    run_id = secrets.token_hex(16)
                    os.mkdir(run_id, mode=0o700, dir_fd=root_fd)
                finally:
                    os.close(root_fd)
                created = _now()
                fd = self._directory(run_id)
                try:
                    _write(
                        fd,
                        "request.json",
                        json_bytes(
                            dict(
                                version=1,
                                request=_request_data(request),
                                owner_scope=owner_scope,
                                created_at=created,
                            )
                        ),
                    )
                    _write(fd, "state.json", json_bytes(_state("PENDING", created)))
                finally:
                    os.close(fd)
                try:
                    threading.Thread(
                        target=self._execute, args=(run_id, request), daemon=True
                    ).start()
                except RuntimeError:
                    fd = self._directory(run_id)
                    try:
                        failure = _failure(_ExecutionFailure("execution", "internal_failure"))
                        _write(
                            fd,
                            "state.json",
                            json_bytes(_state("FAILED", created, finished=_now(), failure=failure)),
                        )
                    finally:
                        os.close(fd)
                    _PROCESS_ACTIVE = False
            except (OSError, OnlineError):
                _PROCESS_ACTIVE = False
                raise OnlineError("unavailable") from None
        return dict(
            run_id=run_id, status="PENDING", request=_request_data(request), created_at=created
        )

    def _execute(self, run_id: str, request: FuturesBasisRequest) -> None:
        global _PROCESS_ACTIVE
        fd = -1
        started = _now()
        try:
            fd = self._directory(run_id)
            created = _read(fd, "state.json", 8192)["created_at"]
            _write(fd, "state.json", json_bytes(_state("RUNNING", created, started)))
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
                payload = json_bytes(reader)
            except Exception:
                raise _ExecutionFailure("result_publication", "serialization_failure") from None
            if len(payload) > MAX_REPORT_BYTES:
                raise _ExecutionFailure("result_publication", "result_too_large")
            if _read(fd, "state.json", 8192)["status"] != "RUNNING":
                return
            _write(fd, "report.json", payload)
            digest = hashlib.sha256(payload).hexdigest()
            if _read(fd, "state.json", 8192)["status"] != "RUNNING":
                return
            _write(
                fd,
                "state.json",
                json_bytes(_state("COMPLETED", created, started, _now(), report.status, digest)),
            )
        except BaseException as exc:
            if fd >= 0:
                failure = _failure(exc)
                try:
                    state = _read(fd, "state.json", 8192)
                    if state["status"] in ("PENDING", "RUNNING"):
                        try:
                            os.unlink("report.json", dir_fd=fd)
                            os.fsync(fd)
                        except FileNotFoundError:
                            pass
                        _write(
                            fd,
                            "state.json",
                            json_bytes(
                                _state(
                                    "FAILED",
                                    state["created_at"],
                                    state["started_at"],
                                    _now(),
                                    failure=failure,
                                )
                            ),
                        )
                except (OnlineError, KeyError):
                    pass
        finally:
            if fd >= 0:
                os.close(fd)
            with _PROCESS_LOCK:
                _PROCESS_ACTIVE = False

    def _owned(self, run_id: str, owner_scope: str) -> tuple[int, dict[str, Any], dict[str, Any]]:
        fd = self._directory(run_id)
        try:
            metadata = _read(fd, "request.json", 8192)
            if not isinstance(metadata, dict) or metadata.get("owner_scope") != owner_scope:
                raise OnlineError("run_not_found")
            if set(metadata) != {"version", "request", "owner_scope", "created_at"}:
                raise OnlineError("corrupt")
            if metadata["version"] != 1:
                raise OnlineError("unsupported_version")
            req = metadata["request"]
            if (
                not isinstance(req, dict)
                or set(req)
                != {"case", "product_code", "start_date", "end_date", "analysis_profile"}
                or req.get("case") != "futures_basis_v1"
                or req.get("analysis_profile") != PROFILE
            ):
                raise OnlineError("corrupt")
            try:
                start = date.fromisoformat(req["start_date"])
                end = date.fromisoformat(req["end_date"])
                if start.isoformat() != req["start_date"] or end.isoformat() != req["end_date"]:
                    raise ValueError
                stored_request = FuturesBasisRequest(req["product_code"], start, end, req["case"])
                validate_request(stored_request, check_today=False)
                if (end - start).days + 1 > 1096:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise OnlineError("corrupt") from None
            state = _read(fd, "state.json", 8192)
            _validate_state(state)
            if state["created_at"] != metadata["created_at"]:
                raise OnlineError("corrupt")
            return fd, metadata, state
        except BaseException:
            os.close(fd)
            raise

    def get_run(self, run_id: str, owner_scope: str) -> dict[str, Any]:
        fd, metadata, state = self._owned(run_id, owner_scope)
        try:
            if state["status"] == "COMPLETED":
                self._check_report_file(fd)
            return dict(
                run_id=run_id,
                request=metadata["request"],
                status=state["status"],
                created_at=state["created_at"],
                started_at=state["started_at"],
                finished_at=state["finished_at"],
                result_available=state["status"] == "COMPLETED",
                result_status=state["result_status"],
                failure=state["failure"],
            )
        finally:
            os.close(fd)

    def get_report(self, run_id: str, owner_scope: str) -> dict[str, Any]:
        if not _READ_PERMIT.acquire(blocking=False):
            raise OnlineError("read_busy")
        try:
            fd, metadata, state = self._owned(run_id, owner_scope)
            try:
                if state["status"] != "COMPLETED":
                    raise OnlineError(
                        "result_not_ready"
                        if state["status"] in ("PENDING", "RUNNING")
                        else "result_unavailable"
                    )
                return self._report(fd, metadata, state)
            finally:
                os.close(fd)
        finally:
            _READ_PERMIT.release()

    def _check_report_file(self, fd: int) -> None:
        try:
            file_fd = os.open("report.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                info = os.fstat(file_fd)
                if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_REPORT_BYTES:
                    raise OnlineError("corrupt")
            finally:
                os.close(file_fd)
        except OSError:
            raise OnlineError("corrupt") from None

    def _report(self, fd: int, metadata: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        # Read bytes once for digest validation; JSON parsing follows only after integrity checks.
        try:
            file_fd = os.open("report.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                info = os.fstat(file_fd)
                if not stat.S_ISREG(info.st_mode):
                    raise OnlineError("corrupt")
                if info.st_size > MAX_REPORT_BYTES:
                    raise OnlineError("response_too_large")
                payload = os.read(file_fd, MAX_REPORT_BYTES + 1)
            finally:
                os.close(file_fd)
        except OSError:
            raise OnlineError("corrupt") from None
        if len(payload) > MAX_REPORT_BYTES:
            raise OnlineError("response_too_large")
        if hashlib.sha256(payload).hexdigest() != state["result_digest"]:
            raise OnlineError("corrupt")
        try:
            reader = _decode(payload)
        except (ValueError, UnicodeError):
            raise OnlineError("corrupt") from None
        if not isinstance(reader, dict):
            raise OnlineError("corrupt")
        if reader.get("profile") != PROFILE_REPORT:
            raise OnlineError("unsupported_version")
        if not isinstance(reader.get("request"), dict):
            raise OnlineError("corrupt")
        if reader.get("status") != state["result_status"] or reader.get("request", {}).get(
            "observation"
        ) != {
            key: metadata["request"][key]
            for key in ("product_code", "start_date", "end_date", "case")
        }:
            raise OnlineError("corrupt")
        if reader.get("request") != json.loads(
            json_bytes(
                standard_report_request(
                    FuturesBasisRequest(
                        metadata["request"]["product_code"],
                        date.fromisoformat(metadata["request"]["start_date"]),
                        date.fromisoformat(metadata["request"]["end_date"]),
                    )
                )
            )
        ):
            raise OnlineError("corrupt")
        if (
            not isinstance(reader.get("fingerprint"), str)
            or re.fullmatch(r"[0-9a-f]{64}", reader["fingerprint"]) is None
            or reader.get("definition_version") != DEFINITION_VERSION
        ):
            raise OnlineError("corrupt")
        return reader


class _ExecutionFailure(Exception):
    def __init__(self, stage: str, category: str, dependency: str | None = None) -> None:
        self.stage, self.category, self.dependency = stage, category, dependency


def _failure(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, _ExecutionFailure):
        stage, category, dependency = exc.stage, exc.category, exc.dependency
    else:
        stage, category, dependency = "execution", "internal_failure", None
    if (
        stage not in FAILURE_CATEGORIES
        or category not in FAILURE_CATEGORIES[stage]
        or (stage == "input_preparation" and dependency not in DEPENDENCIES)
        or (stage != "input_preparation" and dependency is not None)
    ):
        stage, category, dependency = "execution", "internal_failure", None
    reason = _failure_reason(stage, category)
    return dict(stage=stage, category=category, dependency=dependency, reason=reason)
