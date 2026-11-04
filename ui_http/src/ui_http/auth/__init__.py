"""Public Python boundary for Auth registration, identity verification and Operator lifecycle.

Credential verification and current active identity lookup are provided here; persistence
and hashing remain private to Auth.
"""

from ._models import (
    AuthFailureKind,
    AuthServiceError,
    PendingUser,
    RegistrationAccepted,
    UserIdentity,
    UserStatus,
)
from ._service import AuthService, create_service

__all__ = [
    "AuthFailureKind", "AuthService", "AuthServiceError", "PendingUser",
    "RegistrationAccepted", "UserIdentity", "UserStatus", "create_service",
]
