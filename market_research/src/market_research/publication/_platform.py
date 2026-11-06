"""Platform capability required by the Publication V1 storage contract."""

import os

from .errors import PublicationUnavailable


def supports_descriptor_relative_io() -> bool:
    """Return whether descriptor-relative, no-follow filesystem access is available."""
    return (
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_NONBLOCK")
        and all(
            function in os.supports_dir_fd
            for function in (os.open, os.mkdir, os.stat, os.unlink, os.link)
        )
    )


def os_flag(name: str) -> int:
    """Return a platform-specific os flag after capability validation."""
    return int(getattr(os, name))


def require_descriptor_relative_io() -> None:
    """Fail closed when the storage contract cannot be enforced on this platform."""
    if not supports_descriptor_relative_io():
        raise PublicationUnavailable(
            "publication storage requires POSIX descriptor-relative filesystem operations"
        )
