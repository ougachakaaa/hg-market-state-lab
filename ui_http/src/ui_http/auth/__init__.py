"""Public Python boundary for Auth user registration and Operator lifecycle.

G2 will extend this boundary with credential verification and current active identity
lookup. Persistence and hashing remain private to Auth.
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
