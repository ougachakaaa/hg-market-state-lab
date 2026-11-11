"""W2-only POSIX descriptor-relative runtime records and atomic publication."""

import hashlib
import os
import re
import secrets
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from .application_models import FuturesRollRequest
from .online_codec import METADATA_LIMIT, RESULT_LIMIT, decode_request, json_bytes, strict_json
from .online_models import (
    CATEGORIES,
    DEPENDENCIES,
    SAFE_REASONS,
    STAGES,
    TERMINAL,
    FuturesRollOnlineError,
    OnlineFailure,
    OnlineRunStatus,
    RunState,
)

ID_PATTERN = re.compile(r"[0-9a-f]{32}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")


def now() -> str:
    return datetime.now(UTC).isoformat()


def valid_id(run_id: str) -> None:
    if type(run_id) is not str or ID_PATTERN.fullmatch(run_id) is None:
        raise FuturesRollOnlineError("run_not_found")


def supports_storage() -> bool:
    return (
        os.name == "posix"
        and all(hasattr(os, name) for name in ("getuid", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
        and all(op in os.supports_dir_fd for op in (os.open, os.mkdir, os.unlink, os.rename))
        and os.listdir in os.supports_fd
    )


def check_owned(info: os.stat_result, directory: bool = False) -> None:
    if (
        info.st_uid != os.getuid()
        or info.st_mode & 0o022
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        or (not directory and info.st_nlink != 1)
    ):
        raise FuturesRollOnlineError("corrupt")


def read_bytes(fd: int, name: str, limit: int) -> bytes:
    file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        info = os.fstat(file_fd)
        check_owned(info)
        if info.st_size > limit:
            raise FuturesRollOnlineError("corrupt")
        data = bytearray()
        while len(data) <= limit:
            part = os.read(file_fd, min(65536, limit + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > limit or len(data) != info.st_size:
            raise FuturesRollOnlineError("corrupt")
        return bytes(data)
    finally:
        os.close(file_fd)


def atomic_write(fd: int, name: str, data: bytes) -> None:
    temporary = "." + secrets.token_hex(16)
    file_fd = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    try:
        try:
            remaining = memoryview(data)
            while remaining:
                count = os.write(file_fd, remaining)
                if count <= 0:
                    raise OSError("short_write")
                remaining = remaining[count:]
            os.fsync(file_fd)
        finally:
            os.close(file_fd)
        os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=fd)
        except FileNotFoundError:
            pass


def _timestamp(value: Any) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.tzinfo == UTC and parsed.isoformat() == value
    except ValueError:
        return False


def validate_state(state: Any, run_id: str, metadata: dict[str, Any]) -> None:
    if type(state) is not dict or set(state) != {
        "version",
        "run_id",
        "request_digest",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "failure",
        "result_digest",
    }:
        raise ValueError("state_fields")
    status = state["status"]
    if (
        type(state["version"]) is not int
        or state["version"] != 1
        or state["run_id"] != run_id
        or state["request_digest"] != hashlib.sha256(json_bytes(metadata)).hexdigest()
        or type(status) is not str
        or status not in {"PENDING", "RUNNING", *TERMINAL}
        or state["created_at"] != metadata["created_at"]
        or not _timestamp(state["created_at"])
    ):
        raise ValueError("state_identity")
    started, finished = state["started_at"], state["finished_at"]
    if (
        (started is not None and (not _timestamp(started) or started < state["created_at"]))
        or (
            finished is not None
            and (not _timestamp(finished) or finished < (started or state["created_at"]))
        )
        or (status == "PENDING" and started is not None)
        or (status in {"RUNNING", "COMPLETED"} and started is None)
        or (status in TERMINAL) != (finished is not None)
    ):
        raise ValueError("state_timestamps")
    digest = state["result_digest"]
    if status == "COMPLETED":
        if type(digest) is not str or DIGEST_PATTERN.fullmatch(digest) is None:
            raise ValueError("state_digest")
    elif digest is not None:
        raise ValueError("unexpected_digest")
    failure = state["failure"]
    if (status in {"FAILED", "INTERRUPTED"}) != (failure is not None):
        raise ValueError("state_failure")
    if failure is not None:
        if type(failure) is not dict or set(failure) != {
            "stage",
            "category",
            "dependency",
            "reason",
        }:
            raise ValueError("failure_fields")
        stage, category, dependency, reason = (
            failure[k] for k in ("stage", "category", "dependency", "reason")
        )
        if (
            type(stage) is not str
            or stage not in STAGES
            or type(category) is not str
            or type(reason) is not str
            or (
                dependency is not None
                and (type(dependency) is not str or dependency not in DEPENDENCIES)
            )
        ):
            raise ValueError("failure_type")
        if category in {"internal_failure", "interrupted"}:
            if stage != "execution" or reason != category or dependency is not None:
                raise ValueError("execution_failure")
        elif category in {"result_too_large", "serialization_failure", "storage_failure"}:
            if stage != "result_publication" or reason != category or dependency is not None:
                raise ValueError("publication_failure")
        elif category not in CATEGORIES or reason not in SAFE_REASONS:
            raise ValueError("case_failure")
        if status == "INTERRUPTED" and category != "interrupted":
            raise ValueError("interruption_failure")


class FuturesRollRunStore:
    """Private store; callers serialize state mutations, never long computations."""

    def __init__(self, root: Path) -> None:
        if not supports_storage() or not root.is_absolute() or ".." in root.parts:
            raise FuturesRollOnlineError("unavailable")
        self.root = root
        with self._root(create=True) as fd:
            info = os.fstat(fd)
            self.identity = (info.st_dev, info.st_ino)

    @contextmanager
    def _root(self, *, create: bool = False) -> Iterator[int]:
        fd = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in self.root.parts[1:]:
                parent = os.fstat(fd)
                if parent.st_mode & 0o022 and not parent.st_mode & stat.S_ISVTX:
                    raise FuturesRollOnlineError("unavailable")
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            check_owned(os.fstat(fd), directory=True)
            info = os.fstat(fd)
            if hasattr(self, "identity") and self.identity != (info.st_dev, info.st_ino):
                raise FuturesRollOnlineError("corrupt")
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def directory(self, run_id: str) -> Iterator[int]:
        valid_id(run_id)
        with self._root() as root_fd:
            try:
                fd = os.open(run_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
            except FileNotFoundError:
                raise FuturesRollOnlineError("run_not_found") from None
        try:
            check_owned(os.fstat(fd), directory=True)
            yield fd
        finally:
            os.close(fd)

    def create(self, request: FuturesRollRequest, owner: str) -> OnlineRunStatus:
        created = now()
        # Validate bounded metadata before creating any run directory.
        metadata = dict(
            version=1,
            run_id="0" * 32,
            request=asdict(request),
            owner_scope=owner,
            created_at=created,
        )
        try:
            json_bytes(metadata)
        except FuturesRollOnlineError:
            raise FuturesRollOnlineError("invalid_request") from None
        with self._root() as root_fd:
            # Collisions never overwrite or attach to an existing run.
            for _ in range(8):
                run_id = secrets.token_hex(16)
                try:
                    os.mkdir(run_id, mode=0o700, dir_fd=root_fd)
                    break
                except FileExistsError:
                    continue
            else:
                raise FuturesRollOnlineError("unavailable")
            os.fsync(root_fd)
        metadata["run_id"] = run_id
        state = dict(
            version=1,
            run_id=run_id,
            request_digest=hashlib.sha256(json_bytes(metadata)).hexdigest(),
            status="PENDING",
            created_at=created,
            started_at=None,
            finished_at=None,
            failure=None,
            result_digest=None,
        )
        with self.directory(run_id) as fd:
            atomic_write(fd, "request.json", json_bytes(metadata))
            atomic_write(fd, "state.json", json_bytes(state))
        return OnlineRunStatus(run_id, "PENDING", request, created)

    def record(
        self, fd: int, run_id: str, owner: str | None = None
    ) -> tuple[dict[str, Any], dict[str, Any], FuturesRollRequest]:
        metadata = strict_json(read_bytes(fd, "request.json", METADATA_LIMIT))
        # Compare owner before reading state or result; foreign/missing share classification.
        if (
            owner is not None
            and isinstance(metadata, dict)
            and metadata.get("owner_scope") != owner
        ):
            raise FuturesRollOnlineError("run_not_found")
        if (
            type(metadata) is not dict
            or set(metadata) != {"version", "run_id", "request", "owner_scope", "created_at"}
            or type(metadata["version"]) is not int
            or metadata["version"] != 1
            or metadata["run_id"] != run_id
            or type(metadata["owner_scope"]) is not str
            or not metadata["owner_scope"]
            or not _timestamp(metadata["created_at"])
        ):
            raise ValueError("metadata_schema")
        request = decode_request(metadata["request"])
        state = strict_json(read_bytes(fd, "state.json", METADATA_LIMIT))
        validate_state(state, run_id, metadata)
        return metadata, state, request

    def transition(
        self,
        run_id: str,
        status: RunState,
        *,
        failure: OnlineFailure | None = None,
        digest: str | None = None,
    ) -> None:
        with self.directory(run_id) as fd:
            metadata, state, _ = self.record(fd, run_id)
            allowed = {
                "PENDING": {"RUNNING", "FAILED", "INTERRUPTED"},
                "RUNNING": {"COMPLETED", "FAILED", "INTERRUPTED"},
            }
            if status not in allowed.get(state["status"], set()):
                raise FuturesRollOnlineError("corrupt")
            state["status"] = status
            if status == "RUNNING":
                state["started_at"] = now()
            if status in TERMINAL:
                state["finished_at"] = now()
            state["failure"] = asdict(failure) if failure else None
            state["result_digest"] = digest
            validate_state(state, run_id, metadata)
            if status == "COMPLETED":
                payload = read_bytes(fd, "result.json", RESULT_LIMIT)
                if hashlib.sha256(payload).hexdigest() != digest:
                    raise FuturesRollOnlineError("corrupt")
            atomic_write(fd, "state.json", json_bytes(state))

    def status(self, run_id: str, owner: str) -> OnlineRunStatus:
        with self.directory(run_id) as fd:
            _, state, request = self.record(fd, run_id, owner)
            if state["status"] == "COMPLETED":
                result_fd = os.open(
                    "result.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
                )
                try:
                    info = os.fstat(result_fd)
                    check_owned(info)
                    if not 0 < info.st_size <= RESULT_LIMIT:
                        raise FuturesRollOnlineError("corrupt")
                finally:
                    os.close(result_fd)
            return OnlineRunStatus(
                run_id,
                cast(RunState, state["status"]),
                request,
                state["created_at"],
                state["started_at"],
                state["finished_at"],
                OnlineFailure(**state["failure"]) if state["failure"] else None,
            )

    def publish(self, run_id: str, payload: bytes) -> None:
        with self.directory(run_id) as fd:
            _, state, _ = self.record(fd, run_id)
            if state["status"] != "RUNNING" or not 0 < len(payload) <= RESULT_LIMIT:
                raise FuturesRollOnlineError("corrupt")
            # A newly admitted run must have no prior result; never repair an injected object.
            try:
                result_fd = os.open(
                    "result.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
                )
            except FileNotFoundError:
                pass
            else:
                os.close(result_fd)
                raise FuturesRollOnlineError("corrupt")
            atomic_write(fd, "result.json", payload)
        self.transition(run_id, "COMPLETED", digest=hashlib.sha256(payload).hexdigest())

    def recover(self, active: tuple[str, str] | None) -> None:
        with self._root() as fd:
            names = os.listdir(fd)
        for name in names:
            if ID_PATTERN.fullmatch(name) is None:
                continue
            if active == (str(self.root), name):
                continue
            with self.directory(name) as fd:
                metadata, state, _ = self.record(fd, name)
            if state["status"] in {"PENDING", "RUNNING"}:
                self.transition(
                    name,
                    "INTERRUPTED",
                    failure=OnlineFailure("execution", "interrupted", None, "interrupted"),
                )
            elif state["status"] == "COMPLETED":
                self.status(name, metadata["owner_scope"])
