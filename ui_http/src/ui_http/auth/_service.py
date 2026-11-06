"""User lifecycle service, independent of HTTP app and CLI parsing."""

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

import lab_config

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
            memory_cost=19456,
            time_cost=2,
            parallelism=1,
            salt_len=16,
            type=Type.ID,
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
            str(uuid4()),
            canonical,
            password_hash,
            datetime.now(UTC).isoformat(timespec="microseconds"),
        )
        return RegistrationAccepted()

    def verify_credentials(self, username: str, password: str) -> UserIdentity:
        canonical, validated = _username(username), _password(password)
        record = self._store.find(canonical, by_username=True)
        # Public synthetic hash with the same parameters as stored credentials.
        dummy = (
            "$argon2id$v=19$m=19456,t=2,p=1$c3ludGhldGljLWR1bW15IQ$"
            "CTxQcEifVwN+Lkfcf5eTBsJ3Tc6gOYaekGJCLf3GCVU"
        )
        try:
            self._hasher.verify(record[1] if record else dummy, validated)
        except VerifyMismatchError:
            raise AuthServiceError(AuthFailureKind.AUTHENTICATION_FAILED) from None
        except (VerificationError, InvalidHashError, MemoryError):
            raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE) from None
        if record is None or record[0].status != UserStatus.ACTIVE:
            raise AuthServiceError(AuthFailureKind.AUTHENTICATION_FAILED)
        return record[0]

    def get_active_user(self, user_id: str) -> UserIdentity:
        record = self._store.find(_user_id(user_id))
        if record is None or record[0].status != UserStatus.ACTIVE:
            raise AuthServiceError(AuthFailureKind.AUTHENTICATION_FAILED)
        return record[0]

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
    try:
        configured = lab_config.auth_settings().lab_auth_db_path
        if configured is None:
            path = Path(__file__).resolve().parents[3] / "data" / "auth.sqlite3"
        else:
            path = Path(configured)
            if not path.is_absolute() or "\x00" in configured:
                raise ValueError("Invalid Auth storage configuration")
        return AuthService(UserStore(path))
    except (lab_config.ConfigError, ValueError, OSError):
        raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE) from None
