"""Public Auth values and transport-independent failure classification."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    DISABLED = "disabled"


class AuthFailureKind(StrEnum):
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    INVALID_TRANSITION = "invalid_transition"
    OPERATIONAL_FAILURE = "operational_failure"


class AuthServiceError(Exception):
    """Safe failure; raw credentials, SQL and configuration never enter its text."""

    def __init__(self, kind: AuthFailureKind) -> None:
        self.kind = kind
        super().__init__(
            {
                AuthFailureKind.AUTHENTICATION_FAILED: "Authentication failed.",
                AuthFailureKind.INVALID_INPUT: "Invalid authentication input.",
                AuthFailureKind.NOT_FOUND: "User not found.",
                AuthFailureKind.INVALID_TRANSITION: "Invalid user status transition.",
                AuthFailureKind.OPERATIONAL_FAILURE: "Authentication service unavailable.",
            }[kind]
        )


@dataclass(frozen=True)
class RegistrationAccepted:
    message: str = "Registration request accepted."


@dataclass(frozen=True)
class UserIdentity:
    id: str
    username: str
    status: UserStatus


@dataclass(frozen=True)
class PendingUser(UserIdentity):
    created_at: datetime
