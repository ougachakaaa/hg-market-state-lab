"""Small repository-level entry point for local development."""

from __future__ import annotations

import argparse
import json
import re
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
RESEARCH_STUDIES = ROOT / "market-research" / "src" / "market_research" / "studies"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8011
FRONTEND_PORT = 5173
COMMAND_TIMEOUT = 10
HTTP_TIMEOUT = 2
CHINA_MARKET_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
CLI_DATA_SERVICES = ("csi1000-5d-analysis",)
STUDY_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
STUDY_PACKAGE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


class ResearchStudyError(ValueError):
    """A retained Study cannot be safely discovered or executed."""


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


def _poetry_python(poetry: str) -> tuple[Path | None, str | None]:
    """Inspect the existing repository Poetry environment without creating one."""
    try:
        result = subprocess.run(
            [poetry, "env", "info", "--path"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
        if result.returncode != 0:
            return None, None
        environment = Path(result.stdout.strip())
        if not environment.is_absolute():
            environment = ROOT / environment
        executable = environment / "bin" / "python"
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
        ("market-modeling", ROOT / "market-modeling", True),
        ("market-research", ROOT / "market-research", True),
        ("backend-api", BACKEND_API, True),
        ("web-ui", FRONTEND, True),
        ("root pyproject", ROOT / "pyproject.toml", False),
        ("root lockfile", ROOT / "poetry.lock", False),
    ):
        exists = path.is_dir() if is_dir else path.is_file()
        print(f"  {label:<20} {'OK' if exists else 'FAIL (missing)'}")
        failed |= not exists

    print("\nPython runtime")
    poetry, poetry_version = _tool_version("poetry")
    poetry_status = f"OK ({poetry_version})" if poetry_version else "FAIL (unavailable)"
    print(f"  {'Poetry':<20} {poetry_status}")
    failed |= poetry_version is None

    if poetry_version and poetry is not None:
        python, version = _poetry_python(poetry)
        if python is None:
            python_status = "FAIL (Poetry environment missing)"
        elif python.parent.parent.resolve() != (ROOT / ".venv").resolve():
            python_status = "FAIL (Poetry environment is not root .venv)"
        elif version is None:
            python_status = "FAIL (unable to read version)"
        elif version.split(".")[:2] == ["3", "13"]:
            python_status = f"OK ({version})"
        else:
            python_status = f"FAIL (expected 3.13, found {version})"
    else:
        python_status = "FAIL (unavailable)"
    print(f"  {'root Python 3.13':<20} {python_status}")
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
    if not (ROOT / "pyproject.toml").is_file() or not (ROOT / "poetry.lock").is_file():
        print("backend prerequisites missing: root pyproject.toml or poetry.lock", file=sys.stderr)
        return 1
    if not (BACKEND_API / "scripts" / "api.py").is_file():
        print("backend launcher missing: backend-api/scripts/api.py", file=sys.stderr)
        return 1
    poetry = shutil.which("poetry")
    if poetry is None:
        print("backend prerequisite missing: Poetry", file=sys.stderr)
        return 1
    return _run_foreground(
        [poetry, "run", "python", "backend-api/scripts/api.py"], ROOT
    )


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
    if not (ROOT / "pyproject.toml").is_file() or not (ROOT / "poetry.lock").is_file():
        print("data prerequisites missing: root pyproject.toml or poetry.lock", file=sys.stderr)
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
            "market-snapshot/scripts/dms.py",
            "get",
            service_id,
            "--date",
            resolved_date,
        ],
        ROOT,
    )


def _is_regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _study_id(package_name: str) -> str:
    return package_name.replace("_", "-")


def _study_package(study_id: str) -> str:
    return study_id.replace("-", "_")


def _validate_runner(package_dir: Path) -> None:
    if package_dir.is_symlink() or not package_dir.is_dir():
        raise ResearchStudyError(f"malformed Study package: {package_dir.name!r}")
    if STUDY_PACKAGE.fullmatch(package_dir.name) is None:
        raise ResearchStudyError(f"malformed Study package name: {package_dir.name!r}")
    initializer = package_dir / "__init__.py"
    runner = package_dir / "cli.py"
    if not _is_regular_file(initializer):
        raise ResearchStudyError(
            f"malformed Study {_study_id(package_dir.name)!r}: __init__.py is not a regular file"
        )
    if not _is_regular_file(runner):
        raise ResearchStudyError(
            f"malformed Study {_study_id(package_dir.name)!r}: cli.py is not a regular file"
        )


def discover_research_studies() -> tuple[str, ...]:
    """Discover runnable retained Studies without importing Research code."""
    if RESEARCH_STUDIES.is_symlink() or not RESEARCH_STUDIES.is_dir():
        raise ResearchStudyError(f"Research studies root is unavailable: {RESEARCH_STUDIES}")

    study_ids: list[str] = []
    for candidate in RESEARCH_STUDIES.iterdir():
        if candidate.is_symlink():
            raise ResearchStudyError(f"malformed Study package symlink: {candidate.name!r}")
        if not candidate.is_dir():
            continue
        runner = candidate / "cli.py"
        if not runner.exists() and not runner.is_symlink():
            continue
        _validate_runner(candidate)
        study_ids.append(_study_id(candidate.name))
    return tuple(sorted(study_ids))


def research_list() -> int:
    try:
        study_ids = discover_research_studies()
    except (OSError, ResearchStudyError) as error:
        print(f"research discovery error: {error}", file=sys.stderr)
        return 1
    for study_id in study_ids:
        print(study_id)
    return 0


def research_run(study_id: str, study_args: Sequence[str]) -> int:
    if STUDY_ID.fullmatch(study_id) is None:
        print(f"malformed Study ID: {study_id!r}", file=sys.stderr)
        return 2

    package_name = _study_package(study_id)
    package_dir = RESEARCH_STUDIES / package_name
    if package_dir.is_symlink():
        print(f"malformed Study {study_id!r}: package must not be a symlink", file=sys.stderr)
        return 2
    if not package_dir.exists():
        print(f"unknown Study: {study_id!r}", file=sys.stderr)
        return 2
    if not package_dir.is_dir():
        print(f"malformed Study {study_id!r}: package path is not a directory", file=sys.stderr)
        return 2
    runner = package_dir / "cli.py"
    if not runner.exists() and not runner.is_symlink():
        print(f"non-executable Study: {study_id!r} has no cli.py", file=sys.stderr)
        return 2
    try:
        _validate_runner(package_dir)
    except ResearchStudyError as error:
        print(str(error), file=sys.stderr)
        return 2

    module = f"market_research.studies.{package_name}.cli"
    return _run_foreground([sys.executable, "-m", module, *study_args], ROOT)


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

    research_parser = subparsers.add_parser(
        "research", help="Discover and run retained Research Studies."
    )
    research_subparsers = research_parser.add_subparsers(
        dest="research_command", required=True
    )
    research_subparsers.add_parser("list", help="List runnable retained Studies.")
    research_run_parser = research_subparsers.add_parser(
        "run",
        add_help=False,
        help="Forward execution to a study-local CLI.",
    )
    research_run_parser.add_argument("study_id", help="Stable retained Study ID.")
    research_run_parser.add_argument("study_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "data":
        return data(args.service_id, args.target_trade_date)
    if args.command == "research":
        if args.research_command == "list":
            return research_list()
        return research_run(args.study_id, args.study_args)
    return {"doctor": doctor, "backend": backend, "frontend": frontend}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
