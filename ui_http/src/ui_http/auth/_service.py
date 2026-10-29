"""User lifecycle service, independent of HTTP app and CLI parsing."""

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import HashingError
from argon2.low_level import Type

from ._models import (
    AuthFailureKind,
    AuthServiceError,
    PendingUser,
    RegistrationAccepted,
    UserIdentity,
    UserStatus,
)
from ._storage import UserStore

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _username(value: object) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT)
    canonical = value.strip(" ").translate(_ASCII_LOWER)
    if re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", canonical) is None:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT)
    return canonical


def _password(value: object) -> str:
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT)
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT) from None
    if len(encoded) > 512:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT)
    return value


def _user_id(value: object) -> str:
    if not isinstance(value, str):
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT)
    try:
        return str(UUID(value))
    except ValueError:
        raise AuthServiceError(AuthFailureKind.INVALID_INPUT) from None


class AuthService:
    """Use create_service() for the shared Auth storage composition."""

    def __init__(self, store: UserStore) -> None:
        self._store = store
        self._hasher = PasswordHasher(
            memory_cost=19456, time_cost=2, parallelism=1, salt_len=16, type=Type.ID,
        )

    def register(self, username: str, password: str) -> RegistrationAccepted:
        canonical = _username(username)
        validated = _password(password)
        try:
            # Always hash once, before any existence check, including duplicate registrations.
            password_hash = self._hasher.hash(validated)
        except (HashingError, MemoryError):
            raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE) from None
        self._store.insert(
            str(uuid4()), canonical, password_hash,
            datetime.now(UTC).isoformat(timespec="microseconds"),
        )
        return RegistrationAccepted()

    def list_pending(self) -> tuple[PendingUser, ...]:
        return self._store.list_pending()

    def approve(self, user_id: str) -> UserIdentity:
        return self._store.transition(_user_id(user_id), UserStatus.PENDING, UserStatus.ACTIVE)

    def reject(self, user_id: str) -> UserIdentity:
        return self._store.transition(_user_id(user_id), UserStatus.PENDING, UserStatus.REJECTED)

    def disable(self, user_id: str) -> UserIdentity:
        return self._store.transition(_user_id(user_id), UserStatus.ACTIVE, UserStatus.DISABLED)


def create_service() -> AuthService:
    """Resolve the Auth DB once, without CWD, JWT config or HTTP initialization."""
    configured = os.environ.get("LAB_AUTH_DB_PATH")
    try:
        if configured is None:
            path = Path(__file__).resolve().parents[3] / "data" / "auth.sqlite3"
        else:
            path = Path(configured)
            if not path.is_absolute() or "\x00" in configured:
                raise ValueError("Invalid Auth storage configuration")
        return AuthService(UserStore(path))
    except (ValueError, OSError):
        raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE) from None
