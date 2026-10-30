"""Operator delegation, safe delivery, import isolation and real CLI lifecycle."""

import ast
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from ui_cli import auth, cli
from ui_http.auth import (
    AuthFailureKind,
    AuthServiceError,
    PendingUser,
    UserIdentity,
    UserStatus,
    create_service,
)

USER_ID = str(uuid4())
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAB_AUTH_DB_PATH", str(tmp_path / "users.sqlite3"))
    monkeypatch.delenv("LAB_AUTH_JWT_SECRET", raising=False)


@pytest.mark.parametrize("operation,status", [
    ("approve", UserStatus.ACTIVE), ("reject", UserStatus.REJECTED),
    ("disable", UserStatus.DISABLED),
])
def test_state_commands_delegate_and_deliver_only_public_identity(
    operation: str, status: UserStatus, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def change(user_id: str) -> UserIdentity:
        calls.append(user_id)
        return UserIdentity(user_id, "alice", status)

    service = SimpleNamespace(approve=change, reject=change, disable=change)
    monkeypatch.setattr(auth, "create_service", lambda: service)
    assert cli.main(["auth", operation, USER_ID]) == 0
    assert calls == [USER_ID]
    output = capsys.readouterr()
    assert output.out == f"{USER_ID}\talice\t{status}\n"
    assert not output.err


def test_pending_preserves_service_order_and_empty_is_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    users: tuple[PendingUser, ...] = (
        PendingUser(USER_ID, "zulu", UserStatus.PENDING, timestamp),
        PendingUser(str(uuid4()), "alice", UserStatus.PENDING, timestamp),
    )
    monkeypatch.setattr(auth, "create_service", lambda: SimpleNamespace(list_pending=lambda: users))
    assert cli.main(["auth", "pending"]) == 0
    output = capsys.readouterr().out
    assert output.index("zulu") < output.index("alice")
    for user in users:
        assert user.id in output and user.created_at.isoformat() in output
    users = ()
    assert cli.main(["auth", "pending"]) == 0
    assert capsys.readouterr().out == "No pending registration requests.\n"


@pytest.mark.parametrize("kind,exit_code", [
    (AuthFailureKind.INVALID_INPUT, 2), (AuthFailureKind.NOT_FOUND, 2),
    (AuthFailureKind.INVALID_TRANSITION, 2), (AuthFailureKind.OPERATIONAL_FAILURE, 1),
])
@pytest.mark.parametrize("stage", ["composition", "operation"])
def test_failure_classification_and_redaction(
    kind: AuthFailureKind, exit_code: int, stage: str, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sensitive = "SELECT password_hash FROM users; synthetic-password $argon2id$ SECRET"

    def fail(*args: Any) -> Any:
        error = AuthServiceError(kind)
        error.args = (sensitive,)
        raise error

    monkeypatch.setattr(
        auth, "create_service",
        fail if stage == "composition" else lambda: SimpleNamespace(list_pending=fail),
    )
    assert cli.main(["auth", "pending"]) == exit_code
    output = capsys.readouterr()
    assert not output.out
    assert output.err.strip()
    assert all(value not in output.err for value in (
        "password_hash", "synthetic-password", "$argon2id$", "SECRET", "SELECT",
    ))


@pytest.mark.parametrize("arguments", [
    ["auth"], ["auth", "pending", USER_ID], ["auth", "approve"],
    ["auth", "approve", "not-a-uuid"], ["auth", "register"], ["auth", "login"],
    ["auth", "pending", "--db", "elsewhere.sqlite3"],
])
def test_invalid_cli_arguments_never_call_service(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden() -> Any:
        raise AssertionError("Parsing error reached Auth service")

    monkeypatch.setattr(auth, "create_service", forbidden)
    with pytest.raises(SystemExit) as failure:
        cli.main(arguments)
    assert failure.value.code == 2


def run_cli(*arguments: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("lab")
    assert executable is not None
    return subprocess.run(
        [executable, "auth", *arguments],
        cwd=cwd, text=True, capture_output=True, check=False, timeout=20,
    )


def test_real_service_and_cli_persisted_lifecycle(tmp_path: Path) -> None:
    service = create_service()
    service.register(" Alice ", "synthetic-cli-password")
    service.register("bobby", "synthetic-cli-password")
    pending = service.list_pending()
    alice = next(user for user in pending if user.username == "alice")
    bobby = next(user for user in pending if user.username == "bobby")
    listed = run_cli("pending", cwd=tmp_path)
    assert listed.returncode == 0 and alice.id in listed.stdout and bobby.id in listed.stdout
    for operation, user, status in (
        ("approve", alice, "active"), ("approve", alice, "active"),
        ("reject", bobby, "rejected"), ("disable", alice, "disabled"),
    ):
        result = run_cli(operation, user.id, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout == f"{user.id}\t{user.username}\t{status}\n"
    assert create_service().list_pending() == ()
    assert run_cli("pending").returncode == 0
    assert run_cli("approve", bobby.id).returncode == 2
    assert run_cli("reject", str(uuid4())).returncode == 2
    assert "password" not in str(asdict(alice))


def test_concurrent_process_registration(tmp_path: Path) -> None:
    code = (
        "from ui_http.auth import create_service; "
        "create_service().register('Alice', 'synthetic-process-password')"
    )
    processes = [
        subprocess.Popen([sys.executable, "-c", code], cwd=tmp_path,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(4)
    ]
    for process in processes:
        output, errors = process.communicate(timeout=20)
        assert process.returncode == 0, errors
        assert not output
    assert len(create_service().list_pending()) == 1


@pytest.mark.parametrize("command", ["import ui_http.auth", "from ui_cli.cli import main; "
                                   "assert main(['auth', 'pending']) == 0"])
def test_auth_import_and_cli_work_with_http_and_market_imports_blocked(
    tmp_path: Path, command: str,
) -> None:
    code = """
import importlib.abc
import sys
class BlockRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
            'fastapi', 'uvicorn', 'jwt', 'data_snapshot', 'data_lake',
            'market_research', 'market_statistics', 'tushare',
        } or fullname == 'ui_http.app':
            raise AssertionError('Forbidden runtime import: ' + fullname)
sys.meta_path.insert(0, BlockRuntime())
""" + command + "\nassert 'ui_http.app' not in sys.modules\n"
    env = dict(os.environ, LAB_AUTH_JWT_SECRET="invalid-must-not-be-read",
               LAB_AUTH_MODE="invalid-must-not-be-read")
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_imports_only_public_auth_and_never_sqlite_or_hashing() -> None:
    for source in (ROOT / "ui_cli").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
                if node.module == "ui_http.auth":
                    assert {alias.name for alias in node.names} <= {
                        "AuthFailureKind", "AuthServiceError", "create_service",
                    }
            else:
                continue
            for name in names:
                if name.startswith("ui_http"):
                    assert name == "ui_http.auth", source
                assert name.split(".")[0] not in {"sqlite3", "argon2"}, source
