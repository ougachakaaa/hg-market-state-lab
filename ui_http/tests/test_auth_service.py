"""G1 lifecycle acceptance against isolated, real SQLite and Argon2id."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import HashingError, VerifyMismatchError
from argon2.low_level import Type

from ui_http.auth import (
    AuthFailureKind,
    AuthServiceError,
    RegistrationAccepted,
    UserStatus,
    create_service,
)

PASSWORD = "synthetic-test-password"


@pytest.fixture(autouse=True)
def auth_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "auth" / "users.sqlite3"
    monkeypatch.setenv("LAB_AUTH_DB_PATH", str(path))
    monkeypatch.delenv("LAB_AUTH_JWT_SECRET", raising=False)
    return path


def rows(path: Path) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(path)) as connection:
        return connection.execute(
            "SELECT id, username, password_hash, status, created_at FROM users ORDER BY id"
        ).fetchall()


def set_status(status: str) -> str:
    service = create_service()
    service.register("alice", PASSWORD)
    user_id = service.list_pending()[0].id
    if status in {"active", "disabled"}:
        service.approve(user_id)
    if status == "disabled":
        service.disable(user_id)
    if status == "rejected":
        service.reject(user_id)
    return user_id


def test_registration_persistence_safe_views_and_argon2id(auth_db: Path) -> None:
    before = datetime.now(UTC)
    assert create_service().register(" Alice ", PASSWORD) == RegistrationAccepted()
    pending, = create_service().list_pending()
    assert pending.username == "alice"
    assert pending.status == UserStatus.PENDING
    assert str(UUID(pending.id)) == pending.id
    assert before <= pending.created_at <= datetime.now(UTC)
    assert pending.created_at.tzinfo == UTC
    assert set(asdict(pending)) == {"id", "username", "status", "created_at"}
    record, = rows(auth_db)
    params = extract_parameters(record[2])
    assert params.type == Type.ID
    assert params.memory_cost >= 19456
    assert params.time_cost >= 2
    assert params.parallelism >= 1
    assert params.salt_len >= 16
    assert PasswordHasher().verify(record[2], PASSWORD)
    assert PASSWORD.encode() not in auth_db.read_bytes()
    assert PASSWORD not in repr(pending)


@pytest.mark.parametrize("status", ["pending", "active", "rejected", "disabled"])
def test_duplicate_registration_hashes_once_and_never_changes_account(
    status: str, auth_db: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_status(status)
    original = rows(auth_db)
    calls = []
    real_hash = PasswordHasher.hash

    def hash_once(self: PasswordHasher, password: str) -> str:
        calls.append(password)
        return real_hash(self, password)

    monkeypatch.setattr(PasswordHasher, "hash", hash_once)
    assert create_service().register(" ALICE ", "different-test-password") == RegistrationAccepted()
    assert calls == ["different-test-password"]
    assert rows(auth_db) == original


def test_concurrent_first_registration_has_one_winner(auth_db: Path) -> None:
    barrier = Barrier(8)

    def register(number: int) -> RegistrationAccepted:
        barrier.wait()
        return create_service().register(" Alice ", f"synthetic-password-{number}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(register, range(8)))
    assert results == [RegistrationAccepted()] * 8
    assert len(rows(auth_db)) == 1
    assert len(create_service().list_pending()) == 1
    assert sorted(path.name for path in auth_db.parent.iterdir()) == [auth_db.name]


@pytest.mark.parametrize("username", [
    None, 123, b"alice", "", "ab", "a" * 65, " " + "a" * 64,
    "\talice", "alice\n", "Ａlice", "Älice", "ali ce", "_alice", "alice\x00",
    "alice\ud800", "Kelvin",
])
def test_username_validation_precedes_hashing(
    username: Any, auth_db: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("Invalid input reached hashing")

    monkeypatch.setattr(PasswordHasher, "hash", forbidden)
    with pytest.raises(AuthServiceError) as failure:
        create_service().register(username, PASSWORD)
    assert failure.value.kind == AuthFailureKind.INVALID_INPUT
    assert not auth_db.exists()


@pytest.mark.parametrize("password", [None, 123, b"password", "a" * 11, "a" * 129,
                                          "valid-length\ud800"])
def test_password_validation_precedes_hashing(
    password: Any, auth_db: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("Invalid input reached hashing")

    monkeypatch.setattr(PasswordHasher, "hash", forbidden)
    with pytest.raises(AuthServiceError) as failure:
        create_service().register("alice", password)
    assert failure.value.kind == AuthFailureKind.INVALID_INPUT
    assert not auth_db.exists()


@pytest.mark.parametrize("username,password", [
    ("a.b", "a" * 12), ("A" * 64, "a" * 128), ("0_-", "😀" * 128),
    (" alice ", "   test password   "), ("abc", "x" * 11 + "\x00"),
])
def test_valid_boundaries_and_password_preservation(
    username: str, password: str, auth_db: Path,
) -> None:
    create_service().register(username, password)
    record, = rows(auth_db)
    assert PasswordHasher().verify(record[2], password)
    if password != password.strip():
        with pytest.raises(VerifyMismatchError):
            PasswordHasher().verify(record[2], password.strip())


def test_random_salts_and_database_username_uniqueness(auth_db: Path) -> None:
    service = create_service()
    service.register("alice", PASSWORD)
    service.register("bobby", PASSWORD)
    records = rows(auth_db)
    assert records[0][2] != records[1][2]
    with closing(sqlite3.connect(auth_db)) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), "alice", records[0][2], "pending", records[0][4]),
            )


def test_pending_order_uses_timestamp_then_id(auth_db: Path) -> None:
    service = create_service()
    for name in ("alice", "bobby", "carol"):
        service.register(name, PASSWORD)
    with closing(sqlite3.connect(auth_db)) as connection, connection:
        connection.execute("UPDATE users SET created_at = '2026-01-01T00:00:00.000000+00:00'")
        connection.execute(
            "UPDATE users SET created_at = '2025-01-01T00:00:00.000000+00:00' "
            "WHERE username='carol'"
        )
    pending = service.list_pending()
    assert pending[0].username == "carol"
    assert pending == tuple(sorted(pending, key=lambda user: (user.created_at, user.id)))


@pytest.mark.parametrize("status", ["pending", "active", "rejected", "disabled"])
@pytest.mark.parametrize("operation,source,target", [
    ("approve", "pending", "active"), ("reject", "pending", "rejected"),
    ("disable", "active", "disabled"),
])
def test_full_state_matrix_and_persisted_idempotence(
    status: str, operation: str, source: str, target: str, auth_db: Path,
) -> None:
    user_id = set_status(status)
    original = rows(auth_db)[0]
    service = create_service()
    command = getattr(service, operation)
    if status not in {source, target}:
        with pytest.raises(AuthServiceError) as failure:
            command(user_id)
        assert failure.value.kind == AuthFailureKind.INVALID_TRANSITION
        assert rows(auth_db) == [original]
    else:
        identity = command(user_id)
        assert asdict(identity) == {"id": user_id, "username": "alice", "status": target}
        after = rows(auth_db)[0]
        assert after[:3] == original[:3] and after[4] == original[4]
        assert after[3] == target
        assert command(user_id) == identity
        assert rows(auth_db) == [after]
        assert create_service().list_pending() == ()


def test_competing_approve_and_reject_are_serialized(auth_db: Path) -> None:
    user_id = set_status("pending")
    barrier = Barrier(2)

    def change(operation: str) -> str:
        barrier.wait()
        try:
            return getattr(create_service(), operation)(user_id).status
        except AuthServiceError as error:
            return error.kind

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(change, ["approve", "reject"]))
    assert results.count(AuthFailureKind.INVALID_TRANSITION) == 1
    assert rows(auth_db)[0][3] in {"active", "rejected"}
    assert rows(auth_db)[0][3] in results


def test_concurrent_idempotent_approvals(auth_db: Path) -> None:
    user_id = set_status("pending")
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: create_service().approve(user_id), range(4)))
    assert results == [results[0]] * 4
    assert rows(auth_db)[0][3] == "active"


@pytest.mark.parametrize("operation", ["approve", "reject", "disable"])
def test_unknown_and_invalid_user_ids(operation: str) -> None:
    command = getattr(create_service(), operation)
    with pytest.raises(AuthServiceError) as failure:
        command(str(uuid4()))
    assert failure.value.kind == AuthFailureKind.NOT_FOUND
    for invalid in ("alice", "';DROP TABLE users;--", None, 42):
        with pytest.raises(AuthServiceError) as failure:
            command(invalid)
        assert failure.value.kind == AuthFailureKind.INVALID_INPUT


@pytest.mark.parametrize("payload", [b"", b"not-a-sqlite-database"])
def test_existing_empty_or_corrupt_file_is_never_recreated(auth_db: Path, payload: bytes) -> None:
    auth_db.parent.mkdir()
    auth_db.write_bytes(payload)
    with pytest.raises(AuthServiceError) as failure:
        create_service().list_pending()
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE
    assert auth_db.read_bytes() == payload


@pytest.mark.parametrize("mutation", [
    "PRAGMA user_version=99", "DROP TABLE users", "ALTER TABLE users ADD COLUMN unexpected TEXT",
    "CREATE TABLE unrelated(value TEXT)",
    "CREATE TRIGGER unexpected AFTER INSERT ON users BEGIN DELETE FROM users; END",
])
def test_incompatible_schema_never_rebuilt(auth_db: Path, mutation: str) -> None:
    set_status("pending")
    with closing(sqlite3.connect(auth_db)) as connection, connection:
        connection.execute(mutation)
    original = auth_db.read_bytes()
    with pytest.raises(AuthServiceError) as failure:
        create_service().register("bobby", PASSWORD)
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE
    assert auth_db.read_bytes() == original


@pytest.mark.parametrize("mutation", [
    "UPDATE users SET created_at='invalid'",
    "UPDATE users SET created_at='2026-01-01T00:00:00'",
    "UPDATE users SET id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'",
])
def test_invalid_stored_identity_fails_safely(auth_db: Path, mutation: str) -> None:
    set_status("pending")
    with closing(sqlite3.connect(auth_db)) as connection, connection:
        connection.execute(mutation)
    with pytest.raises(AuthServiceError) as failure:
        create_service().list_pending()
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE


@pytest.mark.parametrize("configured", ["relative.sqlite3", "", "bad\x00path"])
def test_invalid_storage_configuration_is_operational_failure(
    monkeypatch: pytest.MonkeyPatch, configured: str,
) -> None:
    # Environment cannot hold NUL, but the config resolver still rejects it explicitly.
    if "\x00" in configured:
        monkeypatch.setattr("ui_http.auth._service.os.environ", {"LAB_AUTH_DB_PATH": configured})
    else:
        monkeypatch.setenv("LAB_AUTH_DB_PATH", configured)
    with pytest.raises(AuthServiceError) as failure:
        create_service()
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE


def test_unwritable_database_target_and_hash_failure_are_safe(
    auth_db: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_db.mkdir(parents=True)
    with pytest.raises(AuthServiceError) as failure:
        create_service().register("alice", PASSWORD)
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE
    assert str(auth_db) not in str(failure.value)

    def failed_hash(*args: Any, **kwargs: Any) -> str:
        raise HashingError("synthetic sensitive hash failure")

    monkeypatch.setattr(PasswordHasher, "hash", failed_hash)
    with pytest.raises(AuthServiceError) as failure:
        create_service().register("alice", PASSWORD)
    assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE
    assert "sensitive" not in str(failure.value)
    assert failure.value.__suppress_context__


def test_locked_storage_does_not_report_registration_accepted(
    auth_db: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_status("pending")
    original = rows(auth_db)
    connect = sqlite3.connect

    def short_timeout(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        kwargs["timeout"] = 0.01
        return connect(*args, **kwargs)

    with closing(connect(auth_db)) as writer:
        writer.execute("BEGIN IMMEDIATE")
        monkeypatch.setattr(sqlite3, "connect", short_timeout)
        with pytest.raises(AuthServiceError) as failure:
            create_service().register("alice", "different-test-password")
        assert failure.value.kind == AuthFailureKind.OPERATIONAL_FAILURE
    assert rows(auth_db) == original


def test_storage_path_resolution_is_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = create_service()
    service.register("alice", PASSWORD)
    monkeypatch.chdir(tmp_path)
    assert create_service().list_pending() == service.list_pending()
    monkeypatch.delenv("LAB_AUTH_DB_PATH")
    # Inspect composition only: never open or mutate the real default DB in tests.
    expected = Path(__file__).resolve().parents[1] / "data" / "auth.sqlite3"
    assert create_service()._store.path == expected
