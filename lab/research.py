"""Discover and forward runnable retained Research Studies."""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path

from . import ROOT
from .process import run_python

RESEARCH_STUDIES = ROOT / "market-research" / "studies"
STUDY_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
STUDY_PACKAGE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


class ResearchStudyError(ValueError):
    """A retained Study cannot be safely discovered or executed."""


def _is_regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _study_id(package_name: str) -> str:
    return package_name.replace("_", "-")


def _study_package(study_id: str) -> str:
    return study_id.replace("-", "_")


def _source_package(owner: Path) -> Path:
    return owner / "src" / "market_research" / "studies" / owner.name


def _validate_runner(package_dir: Path) -> None:
    if package_dir.is_symlink() or not package_dir.is_dir():
        raise ResearchStudyError(f"malformed Study package: {package_dir.name!r}")
    if STUDY_PACKAGE.fullmatch(package_dir.name) is None:
        raise ResearchStudyError(f"malformed Study package name: {package_dir.name!r}")
    owner = package_dir
    package_dir = _source_package(owner)
    for path in (
        owner / "src",
        owner / "src/market_research",
        owner / "src/market_research/studies",
        package_dir,
    ):
        if path.is_symlink():
            raise ResearchStudyError(f"malformed Study package symlink: {owner.name!r}")
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
        runner = _source_package(candidate) / "cli.py"
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
    runner = _source_package(package_dir) / "cli.py"
    if not runner.exists() and not runner.is_symlink():
        print(f"non-executable Study: {study_id!r} has no cli.py", file=sys.stderr)
        return 2
    try:
        _validate_runner(package_dir)
    except ResearchStudyError as error:
        print(str(error), file=sys.stderr)
        return 2

    module = f"market_research.studies.{package_name}.cli"
    return run_python(["-m", module, *study_args], ROOT)
