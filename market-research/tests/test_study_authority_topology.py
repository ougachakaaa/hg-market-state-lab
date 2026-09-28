"""Navigation checks for retained Study authority graphs."""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
STUDIES_ROOT = RESEARCH_ROOT / "studies"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


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


def test_each_study_entry_reaches_its_specialized_authority() -> None:
    for study_root in STUDIES_ROOT.iterdir():
        if not study_root.is_dir():
            continue
        entry = study_root / "ARCHITECTURE.md"
        assert entry.is_file(), study_root
        authority_files = {path.resolve() for path in study_root.rglob("*.md")}
        assert authority_files <= reached_authorities(entry, study_root), study_root


def test_single_and_specialized_study_navigation(tmp_path: Path) -> None:
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


def test_creation_entry_does_not_link_to_legacy_shared_semantics() -> None:
    entry = (STUDIES_ROOT / "AUTHORING.md").read_text(encoding="utf-8")
    assert "(SCHEMA.md)" in entry
    assert "(REVIEW.md)" in entry
    assert "(COMPATIBILITY.md)" in entry
    assert "../shared/" not in entry
