"""Navigation checks for retained Study authority graphs."""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path

import pytest

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
STUDIES_ROOT = RESEARCH_ROOT / "studies"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
REQUIRED_TOP_LEVEL = ("ARCHITECTURE.md", "INPUTS.md", "METHOD.md", "RESULTS.md")
# These authorities predate the fixed top-level layout; new Study directories must use it.
LEGACY_STUDIES = frozenset(
    {
        "cffex_basis_forward_return_association",
        "im_basis_baseline",
        "im_basis_forward_return_association",
        "price_to_lagged_ma_distribution",
        "price_to_lagged_ma_short_horizon_reversion",
    }
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


def test_each_study_entry_reaches_its_specialized_authority() -> None:
    for study_root in STUDIES_ROOT.iterdir():
        if not study_root.is_dir():
            continue
        entry = study_root / "ARCHITECTURE.md"
        assert entry.is_file(), study_root
        authority_files = {path.resolve() for path in study_root.rglob("*.md")}
        assert authority_files <= reached_authorities(entry, study_root), study_root
        if study_root.name not in LEGACY_STUDIES:
            assert_new_study_topology(study_root)


def test_mo_option_risk_premium_authority_links_resolve() -> None:
    study_root = STUDIES_ROOT / "mo_option_risk_premium_baseline"
    for path in study_root.glob("*.md"):
        for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0]
            if target and "://" not in target:
                assert (path.parent / target).is_file(), (path, raw_target)


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
    assert "../shared/" not in entry
    skeleton = STUDIES_ROOT / "SKELETON.md"
    assert skeleton.is_file()
    assert skeleton.resolve() in local_study_links(authoring, STUDIES_ROOT)
    layout = skeleton.read_text(encoding="utf-8")
    assert "studies/<study_package>/" in layout
    assert all(f"── {name}" in layout for name in REQUIRED_TOP_LEVEL)
    assert all(f"`{name}`" in entry for name in REQUIRED_TOP_LEVEL)
    review = STUDIES_ROOT / "REVIEW.md"
    assert skeleton.resolve() in local_study_links(review, STUDIES_ROOT)
