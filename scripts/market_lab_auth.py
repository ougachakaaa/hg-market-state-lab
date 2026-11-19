"""Shared configuration preflight and readiness for the one-click launchers."""

import json
import os
import secrets
import sys
from http.client import HTTPConnection, HTTPException
from pathlib import Path

import lab_config
from ui_http.auth._session import LOCAL_WEB_ORIGIN, AuthConfig

BACKEND = "127.0.0.1"
FRONTEND_ORIGIN = "http://127.0.0.1:5173"
AUTH_REQUIRED = {
    "error": {
        "kind": "authentication_required",
        "detail": "Authentication required.",
        "param": None,
    }
}


def managed_secret(path: Path) -> str:
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return path.read_text(encoding="ascii").strip()
    secret = secrets.token_urlsafe(32)
    with os.fdopen(fd, "w", encoding="ascii") as file:
        file.write(secret)
    return secret


def prepare(runtime_dir: Path) -> tuple[str, str, str]:
    settings = lab_config.auth_settings()
    if settings.lab_auth_mode == "local":
        return "local", "keep", "keep"
    if settings.lab_auth_mode != "loopback-http":
        raise RuntimeError("The one-click HTTP launcher supports local or loopback-http mode.")

    set_origin = settings.lab_auth_origin is None
    set_secret = settings.lab_auth_jwt_secret is None
    fallback = {}
    if set_origin:
        fallback["lab_auth_origin"] = FRONTEND_ORIGIN
    if set_secret:
        fallback["lab_auth_jwt_secret"] = managed_secret(runtime_dir / "jwt-secret")

    config = AuthConfig.from_settings(settings.model_copy(update=fallback))
    config.validate_listener(BACKEND)
    if config.browser_origin != LOCAL_WEB_ORIGIN:
        raise RuntimeError("The one-click HTTP launcher requires the local frontend origin.")
    return "authenticated", "origin" if set_origin else "keep", "secret" if set_secret else "keep"


def backend_ready(expected: str) -> bool:
    if expected not in {"local", "authenticated"}:
        return False
    connection = HTTPConnection(BACKEND, 8011, timeout=2)
    try:
        connection.request("GET", "/auth/mode")
        mode = connection.getresponse()
        if mode.status != 200 or json.loads(mode.read()) != expected:
            return False
        connection.request("GET", "/research/capabilities")
        access = connection.getresponse()
        if expected == "local":
            return access.status == 200
        return access.status == 401 and json.loads(access.read()) == AUTH_REQUIRED
    except (OSError, HTTPException, ValueError):
        return False
    finally:
        connection.close()


def main() -> int:
    command, value = sys.argv[1:]
    if command == "ready":
        return 0 if backend_ready(value) else 1
    if command == "prepare":
        try:
            print(*prepare(Path(value)))
        except (lab_config.ConfigError, RuntimeError, OSError, UnicodeError):
            print(
                "Invalid authentication configuration for the one-click HTTP launcher.",
                file=sys.stderr,
            )
            return 1
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
