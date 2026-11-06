"""Read-only local repository and service readiness diagnostics."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import lab_config

from . import ROOT
from .process import resolve_executable

MARKET_SNAPSHOT = ROOT / "data_snapshot"
BACKEND_API = ROOT / "ui_http"
FRONTEND = ROOT / "ui_web"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8011
FRONTEND_PORT = 5173
COMMAND_TIMEOUT = 10
HTTP_TIMEOUT = 2


def _tool_version(name: str) -> tuple[str | None, str | None]:
    executable = resolve_executable(name)
    if executable is None:
        return None, None
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return executable, None
    if result.returncode != 0:
        return executable, None
    return executable, result.stdout.strip() or result.stderr.strip()


def _port_listening(port: int) -> bool:
    try:
        with socket.create_connection((BACKEND_HOST, port), timeout=0.5):
            return True
    except OSError:
        return False


def _backend_status() -> str:
    try:
        with urlopen(
            f"http://{BACKEND_HOST}:{BACKEND_PORT}/openapi.json", timeout=HTTP_TIMEOUT
        ) as response:
            document = json.load(response)
            if (
                response.status == 200
                and isinstance(document, dict)
                and "openapi" in document
                and "paths" in document
            ):
                return "running / healthy"
    except HTTPError as error:
        try:
            with error:
                if error.code == 401 and json.load(error) == {"error": {
                    "kind": "authentication_required", "detail": "Authentication required.",
                    "param": None,
                }}:
                    return "running / authentication required"
        except (ValueError, OSError):
            pass
    except Exception:  # A different service or malformed response is an unhealthy local port.
        pass
    return "port occupied / unhealthy" if _port_listening(BACKEND_PORT) else "stopped"


def doctor() -> int:
    failed = False
    print("hg-market-state-lab doctor\n")
    print("repository")
    for label, path, is_dir in (
        ("data_snapshot", MARKET_SNAPSHOT, True),
        ("market_modeling", ROOT / "market_modeling", True),
        ("market_research", ROOT / "market_research", True),
        ("ui_http", BACKEND_API, True),
        ("ui_web", FRONTEND, True),
        ("root pyproject", ROOT / "pyproject.toml", False),
        ("root lockfile", ROOT / "poetry.lock", False),
    ):
        exists = path.is_dir() if is_dir else path.is_file()
        print(f"  {label:<20} {'OK' if exists else 'FAIL (missing)'}")
        failed |= not exists

    print("\nconfiguration")
    env_file = lab_config.ENV_FILE
    print(
        f"  {'root .env':<20} "
        f"{'OK' if env_file.is_file() else 'missing (copy .env.example)'}"
    )
    try:
        token = lab_config.tushare_token()
    except lab_config.ConfigError:
        print(f"  {'TUSHARE_TOKEN':<20} FAIL (invalid configuration)")
        failed = True
    else:
        print(
            f"  {'TUSHARE_TOKEN':<20} "
            f"{'OK (configured)' if token else 'not configured (Source I/O unavailable)'}"
        )

    print("\nPython runtime")
    _, poetry_version = _tool_version("poetry")
    poetry_status = f"OK ({poetry_version})" if poetry_version else "FAIL (unavailable)"
    print(f"  {'Poetry':<20} {poetry_status}")
    failed |= poetry_version is None

    python_version = ".".join(map(str, sys.version_info[:3]))
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        python_status = "FAIL (current Python is not root .venv)"
    elif sys.version_info[:2] == (3, 13):
        python_status = f"OK ({python_version})"
    else:
        python_status = f"FAIL (expected 3.13, found {python_version})"
    print(f"  {'root Python 3.13':<20} {python_status}")
    failed |= not python_status.startswith("OK")

    module_envs = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.iterdir()
        if path.is_dir()
        and path.name not in {".venv", ".git"}
        and (path / ".venv").exists()
    )
    if module_envs:
        print(f"  {'module-local .venv':<20} FAIL ({', '.join(module_envs)})")
        failed = True
    else:
        print(f"  {'module-local .venv':<20} OK (none)")

    launcher = BACKEND_API / "scripts" / "api.py"
    launcher_exists = launcher.is_file()
    print(f"  {'launcher':<20} {'OK' if launcher_exists else 'FAIL (missing)'}")
    failed |= not launcher_exists
    print(f"  {f'{BACKEND_HOST}:{BACKEND_PORT}':<20} {_backend_status()}")

    print("\nfrontend")
    package_exists = (FRONTEND / "package.json").is_file()
    for name in ("node", "npm"):
        _, version = _tool_version(name)
        status = (
            f"OK ({version})"
            if version
            else ("FAIL (unavailable)" if package_exists else "WARN (unavailable)")
        )
        print(f"  {name:<20} {status}")
        failed |= package_exists and version is None
    print(f"  {'package.json':<20} {'OK' if package_exists else 'missing'}")
    frontend_status = "not initialized"
    if package_exists:
        frontend_status = "running" if _port_listening(FRONTEND_PORT) else "stopped"
    print(f"  {'status':<20} {frontend_status}")
    return 1 if failed else 0
