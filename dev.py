"""Small repository-level entry point for local development."""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
MARKET_SNAPSHOT = ROOT / "market-snapshot"
BACKEND_API = ROOT / "backend-api"
FRONTEND = ROOT / "web-ui"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8011
FRONTEND_PORT = 5173
COMMAND_TIMEOUT = 10
HTTP_TIMEOUT = 2
CHINA_MARKET_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
CLI_DATA_SERVICES = ("csi1000-5d-analysis",)


def _tool_version(name: str) -> tuple[str | None, str | None]:
    executable = shutil.which(name)
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


def _poetry_python(poetry: str, project: Path) -> tuple[Path | None, str | None]:
    """Inspect an existing Poetry environment without creating one."""
    try:
        result = subprocess.run(
            [poetry, "env", "info", "--executable"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
        if result.returncode != 0:
            return None, None
        executable = Path(result.stdout.strip())
        if not executable.is_file():
            return None, None
        version = subprocess.run(
            [str(executable), "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if version.returncode != 0:
        return executable, None
    return executable, version.stdout.strip()


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
    except Exception:  # A different service or malformed response is an unhealthy local port.
        pass
    return "port occupied / unhealthy" if _port_listening(BACKEND_PORT) else "stopped"


def doctor() -> int:
    failed = False
    print("hg-market-state-lab doctor\n")
    print("repository")
    for label, path, is_dir in (
        ("market-snapshot", MARKET_SNAPSHOT, True),
        ("backend-api", BACKEND_API, True),
        ("web-ui", FRONTEND, True),
        ("market pyproject", MARKET_SNAPSHOT / "pyproject.toml", False),
        ("backend pyproject", BACKEND_API / "pyproject.toml", False),
    ):
        exists = path.is_dir() if is_dir else path.is_file()
        print(f"  {label:<20} {'OK' if exists else 'FAIL (missing)'}")
        failed |= not exists

    print("\nbackend")
    poetry, poetry_version = _tool_version("poetry")
    poetry_status = f"OK ({poetry_version})" if poetry_version else "FAIL (unavailable)"
    print(f"  {'Poetry':<20} {poetry_status}")
    failed |= poetry_version is None

    for label, project in (
        ("market Python 3.13", MARKET_SNAPSHOT),
        ("backend Python 3.13", BACKEND_API),
    ):
        if poetry_version and project.is_dir():
            python, version = _poetry_python(poetry, project)
            if python is None:
                python_status = "FAIL (Poetry environment missing)"
            elif version is None:
                python_status = "FAIL (unable to read version)"
            elif version.split(".")[:2] == ["3", "13"]:
                python_status = f"OK ({version})"
            else:
                python_status = f"FAIL (expected 3.13, found {version})"
        else:
            python_status = "FAIL (unavailable)"
        print(f"  {label:<20} {python_status}")
        failed |= not python_status.startswith("OK")

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


def _run_foreground(command: list[str], cwd: Path) -> int:
    try:
        child = subprocess.Popen(command, cwd=cwd)
    except OSError as error:
        print(f"unable to start {command[0]}: {error}", file=sys.stderr)
        return 1
    try:
        return child.wait()
    except KeyboardInterrupt:
        # Both processes receive Ctrl+C in the same foreground console. Give the
        # native launcher a chance to exit, then ensure it is not left running.
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait()
        return 130


def backend() -> int:
    if not BACKEND_API.is_dir() or not (BACKEND_API / "pyproject.toml").is_file():
        print("backend prerequisites missing: backend-api/pyproject.toml", file=sys.stderr)
        return 1
    if not (BACKEND_API / "scripts" / "api.py").is_file():
        print("backend launcher missing: backend-api/scripts/api.py", file=sys.stderr)
        return 1
    poetry = shutil.which("poetry")
    if poetry is None:
        print("backend prerequisite missing: Poetry", file=sys.stderr)
        return 1
    return _run_foreground([poetry, "run", "python", "scripts/api.py"], BACKEND_API)


def frontend() -> int:
    if not (FRONTEND / "package.json").is_file():
        print("frontend not initialized: web-ui/package.json not found", file=sys.stderr)
        return 1
    npm = shutil.which("npm")
    if npm is None:
        print("frontend prerequisite missing: npm", file=sys.stderr)
        return 1
    return _run_foreground([npm, "run", "dev"], FRONTEND)


def _china_market_today() -> str:
    """Return today's calendar date in UTC+8, without trading-day adjustment."""
    return datetime.now(CHINA_MARKET_TIMEZONE).date().isoformat()


def data(service_id: str, target_trade_date: str | None = None) -> int:
    """Forward one persisted-artifact Data Service request to the canonical CLI."""
    if not MARKET_SNAPSHOT.is_dir() or not (MARKET_SNAPSHOT / "pyproject.toml").is_file():
        print("data prerequisites missing: market-snapshot/pyproject.toml", file=sys.stderr)
        return 1
    if not (MARKET_SNAPSHOT / "scripts" / "dms.py").is_file():
        print("data launcher missing: market-snapshot/scripts/dms.py", file=sys.stderr)
        return 1
    poetry = shutil.which("poetry")
    if poetry is None:
        print("data prerequisite missing: Poetry", file=sys.stderr)
        return 1

    resolved_date = target_trade_date if target_trade_date is not None else _china_market_today()
    return _run_foreground(
        [
            poetry,
            "run",
            "python",
            "scripts/dms.py",
            "get",
            service_id,
            "--date",
            resolved_date,
        ],
        MARKET_SNAPSHOT,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repository development commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check local development prerequisites.")
    subparsers.add_parser("backend", help="Run the backend development server.")
    subparsers.add_parser("frontend", help="Run the frontend development server.")

    data_parser = subparsers.add_parser(
        "data", help="Forward a persisted-artifact Data Service request to dms."
    )
    data_parser.add_argument(
        "service_id",
        choices=CLI_DATA_SERVICES,
        help="CLI-supported persisted-artifact Data Service id.",
    )
    data_parser.add_argument(
        "--date",
        dest="target_trade_date",
        metavar="YYYY-MM-DD",
        help="Target trade date; defaults to today's Asia/Shanghai calendar date.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "data":
        return data(args.service_id, args.target_trade_date)
    return {"doctor": doctor, "backend": backend, "frontend": frontend}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
