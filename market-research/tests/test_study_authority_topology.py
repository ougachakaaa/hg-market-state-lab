"""Navigation checks for retained Study authority graphs."""

from __future__ import annotations

import ast
import re
from collections import deque
from pathlib import Path

import pytest

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
STUDIES_ROOT = RESEARCH_ROOT / "src/market_research/studies"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
REQUIRED_TOP_LEVEL = ("ARCHITECTURE.md", "INPUTS.md", "METHOD.md", "RESULTS.md")
REQUIRED_IMPLEMENTATION = (
    "__init__.py",
    "cli.py",
    "study.py",
)


def local_study_links(path: Path, study_root: Path) -> set[Path]:
    targets = set()
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.split("#", 1)[0]
        if not target or "://" in target:
            continue
        resolved = (path.parent / target).resolve()
        if resolved.is_relative_to(study_root) and resolved.suffix == ".md":
            targets.add(resolved)
    return targets


def reached_authorities(entry: Path, study_root: Path) -> set[Path]:
    pending = deque([entry.resolve()])
    reached: set[Path] = set()
    while pending:
        current = pending.popleft()
        if current in reached:
            continue
        reached.add(current)
        pending.extend(local_study_links(current, study_root.resolve()))
    return reached


def assert_new_study_topology(study_root: Path) -> None:
    for name in REQUIRED_TOP_LEVEL:
        path = study_root / name
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").strip(), path

    entry = study_root / "ARCHITECTURE.md"
    assert {study_root / name for name in REQUIRED_TOP_LEVEL[1:]} <= local_study_links(
        entry, study_root
    ), entry
    authority_files = {path.resolve() for path in study_root.rglob("*.md")}
    assert authority_files <= reached_authorities(entry, study_root), study_root


def assert_new_runnable_package(
    implementation_root: Path,
    required_helpers: tuple[str, ...] = (),
) -> None:
    assert not implementation_root.with_suffix(".py").exists(), implementation_root
    assert implementation_root.is_dir(), implementation_root
    for name in (*REQUIRED_IMPLEMENTATION, *required_helpers):
        assert (implementation_root / name).is_file(), implementation_root / name
    authority = implementation_root / "ARCHITECTURE.md"
    assert authority.is_file(), authority
    init = ast.parse((implementation_root / "__init__.py").read_text(encoding="utf-8"))
    pointer = "Canonical authority: ARCHITECTURE.md (beside this file)"
    assert pointer in (ast.get_docstring(init) or ""), implementation_root


def test_each_study_entry_reaches_its_specialized_authority() -> None:
    for study_root in STUDIES_ROOT.iterdir():
        if not study_root.is_dir() or not any(study_root.glob("*.md")):
            continue
        entry = study_root / "ARCHITECTURE.md"
        assert entry.is_file(), study_root
        authority_files = {path.resolve() for path in study_root.rglob("*.md")}
        assert authority_files <= reached_authorities(entry, study_root), study_root
        assert_new_study_topology(study_root)


def test_new_runnable_studies_have_semantic_package_boundaries() -> None:
    candidates = {
        path.name
        for path in STUDIES_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__" and any(path.glob("*.py"))
    } | {path.stem for path in STUDIES_ROOT.glob("*.py") if path.name != "__init__.py"}
    for study_package in candidates:
        assert_new_runnable_package(STUDIES_ROOT / study_package)


def test_legacy_single_file_and_specialized_navigation(tmp_path: Path) -> None:
    entry = tmp_path / "ARCHITECTURE.md"
    entry.write_text("# Study entry\n", encoding="utf-8")
    assert reached_authorities(entry, tmp_path) == {entry.resolve()}

    method = tmp_path / "METHOD.md"
    analysis = tmp_path / "method/analyses/linear_association.md"
    analysis.parent.mkdir(parents=True)
    entry.write_text("[Method](METHOD.md)\n", encoding="utf-8")
    method.write_text("[Analysis](method/analyses/linear_association.md)\n", encoding="utf-8")
    analysis.write_text("# Linear association\n", encoding="utf-8")
    assert reached_authorities(entry, tmp_path) == {
        entry.resolve(),
        method.resolve(),
        analysis.resolve(),
    }

    method.write_text("# Method without navigation\n", encoding="utf-8")
    assert analysis.resolve() not in reached_authorities(entry, tmp_path)


def make_new_study(study_root: Path) -> None:
    (study_root / "ARCHITECTURE.md").write_text(
        "# Study entry\n[Inputs](INPUTS.md)\n[Method](METHOD.md)\n[Results](RESULTS.md)\n",
        encoding="utf-8",
    )
    (study_root / "INPUTS.md").write_text(
        "# Inputs\nPopulation and parameters.\n", encoding="utf-8"
    )
    (study_root / "METHOD.md").write_text(
        "# Method\n[Observation](method/observations/outcome.md)\n", encoding="utf-8"
    )
    (study_root / "RESULTS.md").write_text("# Results\nExpected evidence.\n", encoding="utf-8")
    observation = study_root / "method/observations/outcome.md"
    observation.parent.mkdir(parents=True)
    observation.write_text("# Outcome observation\n", encoding="utf-8")


def test_new_study_topology_reaches_deeper_authority(tmp_path: Path) -> None:
    make_new_study(tmp_path)
    assert_new_study_topology(tmp_path)


@pytest.mark.parametrize(
    "invalid", ["missing_file", "missing_link", "empty_file", "orphaned_owner"]
)
def test_new_study_topology_rejects_incomplete_authority(tmp_path: Path, invalid: str) -> None:
    make_new_study(tmp_path)
    if invalid == "missing_file":
        (tmp_path / "INPUTS.md").unlink()
    elif invalid == "missing_link":
        (tmp_path / "ARCHITECTURE.md").write_text(
            "# Study entry\n[Method](METHOD.md)\n[Results](RESULTS.md)\n", encoding="utf-8"
        )
    elif invalid == "empty_file":
        (tmp_path / "RESULTS.md").write_text("\n", encoding="utf-8")
    else:
        (tmp_path / "METHOD.md").write_text(
            "# Method\nObservation details follow.\n", encoding="utf-8"
        )

    with pytest.raises(AssertionError):
        assert_new_study_topology(tmp_path)


def test_creation_entry_does_not_link_to_legacy_shared_semantics() -> None:
    authoring = STUDIES_ROOT / "AUTHORING.md"
    entry = authoring.read_text(encoding="utf-8")
    assert "(SCHEMA.md)" in entry
    assert "(REVIEW.md)" in entry
    assert "(COMPATIBILITY.md)" in entry
    shared_links = [
        target for target in re.findall(r"\]\(([^)]+)\)", entry) if target.startswith("../shared/")
    ]
    assert set(shared_links) == {"../shared/ARCHITECTURE.md"}
    skeleton = STUDIES_ROOT / "SKELETON.md"
    assert skeleton.is_file()
    assert skeleton.resolve() in local_study_links(authoring, STUDIES_ROOT)
    layout = skeleton.read_text(encoding="utf-8")
    assert "studies/<study_package>/" in layout
    assert all(f"── {name}" in layout for name in REQUIRED_TOP_LEVEL)
    assert all(f"`{name}`" in entry for name in REQUIRED_TOP_LEVEL)
    review = STUDIES_ROOT / "REVIEW.md"
    assert skeleton.resolve() in local_study_links(review, STUDIES_ROOT)


def test_implementation_contract_is_reachable_from_authoring_and_review() -> None:
    contract = STUDIES_ROOT / "IMPLEMENTATION.md"
    assert contract.is_file()
    for entry in (
        RESEARCH_ROOT / "ARCHITECTURE.md",
        RESEARCH_ROOT / "AGENTS.md",
        STUDIES_ROOT / "AUTHORING.md",
        STUDIES_ROOT / "REVIEW.md",
    ):
        assert contract.resolve() in local_study_links(entry, RESEARCH_ROOT), entry


def test_new_runnable_package_requires_modules_and_authority_pointer(tmp_path: Path) -> None:
    implementation_root = tmp_path / "src/example_study"
    implementation_root.mkdir(parents=True)
    (implementation_root / "ARCHITECTURE.md").write_text("# Example\n", encoding="utf-8")
    for name in (*REQUIRED_IMPLEMENTATION, "analyses.py", "evidence.py"):
        (implementation_root / name).write_text("", encoding="utf-8")
    (implementation_root / "__init__.py").write_text(
        '"""Canonical authority: ARCHITECTURE.md (beside this file)."""\n',
        encoding="utf-8",
    )
    assert_new_runnable_package(implementation_root)

    (implementation_root / "analyses.py").unlink()
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation_root, ("analyses.py",))
    (implementation_root / "analyses.py").write_text("", encoding="utf-8")

    (implementation_root / "__init__.py").write_text('"""Example Study."""\n', encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation_root)

    (implementation_root / "__init__.py").write_text(
        '"""Canonical authority: ARCHITECTURE.md (beside this file)."""\n',
        encoding="utf-8",
    )
    (implementation_root.with_suffix(".py")).write_text("", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation_root)


@pytest.mark.parametrize("name", REQUIRED_IMPLEMENTATION)
def test_orchestration_package_still_requires_all_mandatory_modules(
    tmp_path: Path,
    name: str,
) -> None:
    implementation = tmp_path / "src/example_study"
    implementation.mkdir(parents=True)
    (implementation / "ARCHITECTURE.md").write_text("# Example\n", encoding="utf-8")
    for module in REQUIRED_IMPLEMENTATION:
        (implementation / module).write_text("", encoding="utf-8")
    (implementation / "__init__.py").write_text(
        '"""Canonical authority: ARCHITECTURE.md (beside this file)."""\n',
        encoding="utf-8",
    )
    assert_new_runnable_package(implementation)
    (implementation / name).unlink()
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation)


def test_new_runnable_study_cannot_be_a_single_script(tmp_path: Path) -> None:
    implementation_root = tmp_path / "src/example_study"
    implementation_root.mkdir(parents=True)
    (implementation_root / "ARCHITECTURE.md").write_text("# Example\n", encoding="utf-8")
    implementation_root.with_suffix(".py").write_text("", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation_root)


def test_runnable_package_rejects_authority_in_a_shadow_directory(tmp_path: Path) -> None:
    implementation = tmp_path / "src/example_study"
    implementation.mkdir(parents=True)
    for module in REQUIRED_IMPLEMENTATION:
        (implementation / module).write_text("", encoding="utf-8")
    (implementation / "__init__.py").write_text(
        '"""Canonical authority: ARCHITECTURE.md (beside this file)."""\n',
        encoding="utf-8",
    )
    shadow = tmp_path / "studies/example_study"
    shadow.mkdir(parents=True)
    (shadow / "ARCHITECTURE.md").write_text("# Shadow authority\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_new_runnable_package(implementation)

    (shadow / "ARCHITECTURE.md").rename(implementation / "ARCHITECTURE.md")
    assert_new_runnable_package(implementation)
