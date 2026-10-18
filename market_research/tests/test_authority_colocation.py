"""Canonical Research owners, progressive disclosure and import compatibility."""

from __future__ import annotations

import ast
import importlib
import re
import unicodedata
from collections import deque
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = REPOSITORY_ROOT / "market_research"

LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")
FRAMEWORK_ENTRIES = {
    "v2": "ARCHITECTURE.md",
    "shared": "ARCHITECTURE.md",
    "observations": "ARCHITECTURE.md",
    "studies": "ARCHITECTURE.md",
    "ui": "ARCHITECTURE.md",
}


def reachable(entry: Path) -> set[Path]:
    pending = deque([entry.resolve()])
    visited: set[Path] = set()
    while pending:
        current = pending.popleft()
        if current in visited:
            continue
        assert current.is_file(), current
        visited.add(current)
        for raw in LINK.findall(current.read_text(encoding="utf-8")):
            target = raw.split("#", 1)[0]
            if target and "://" not in target:
                resolved = (current.parent / target).resolve()
                if resolved.suffix == ".md" and resolved.is_relative_to(RESEARCH_ROOT):
                    pending.append(resolved)
    return visited


def test_all_research_contracts_are_reachable_through_stable_entries() -> None:
    contracts = {
        path.resolve()
        for framework in FRAMEWORK_ENTRIES
        for path in (RESEARCH_ROOT / framework).rglob("*.md")
    }
    contracts.add((RESEARCH_ROOT / "UPSTREAM.md").resolve())
    assert contracts
    for entry in (
        REPOSITORY_ROOT / "ARCHITECTURE.md",
        RESEARCH_ROOT / "ARCHITECTURE.md",
        RESEARCH_ROOT / "AGENTS.md",
    ):
        assert contracts <= reachable(entry), (entry, contracts - reachable(entry))


@pytest.mark.parametrize("framework,entry", FRAMEWORK_ENTRIES.items())
def test_framework_and_concrete_packages_have_owner_authority(framework: str, entry: str) -> None:
    owner = RESEARCH_ROOT / framework
    assert (owner / entry).is_file()
    for init in owner.rglob("__init__.py"):
        package = init.parent
        source = next(parent for parent in package.parents if parent.name == "src")
        canonical_owner = source.parent
        assert not list(source.rglob("*.md"))
        docstring = ast.get_docstring(ast.parse(init.read_text(encoding="utf-8"))) or ""
        pointer = "../../../" if canonical_owner == owner else "../../../../"
        authority = entry if canonical_owner == owner else "ARCHITECTURE.md"
        assert pointer + authority in docstring, init
        assert (canonical_owner / authority).is_file()
        assert (canonical_owner / authority).resolve() in reachable(owner / entry)


def test_authority_only_mirror_trees_are_absent() -> None:
    old = RESEARCH_ROOT / "src/market_research"
    assert not list(old.rglob("*.md"))
    assert not list(old.rglob("*.py"))
    for framework in ("shared", "studies"):
        assert not (RESEARCH_ROOT / framework / "src").exists()


def heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", path.read_text(encoding="utf-8"), re.M):
        slug = "".join(
            char
            for char in heading.strip().lower()
            if char in "_- " or unicodedata.category(char)[0] in "LN"
        ).replace(" ", "-")
        count = occurrences.get(slug, 0)
        occurrences[slug] = count + 1
        anchors.add(f"{slug}-{count}" if count else slug)
    return anchors


def test_research_links_and_fragments_resolve_at_the_colocated_owner() -> None:
    for source in RESEARCH_ROOT.rglob("*.md"):
        for raw in LINK.findall(source.read_text(encoding="utf-8")):
            if "://" in raw or raw.startswith("mailto:"):
                continue
            path, _, fragment = raw.partition("#")
            target = (source.parent / path).resolve() if path else source
            assert target.is_file(), (source, raw)
            if fragment and target.suffix == ".md" and target.is_relative_to(RESEARCH_ROOT):
                assert fragment in heading_anchors(target), (source, raw)


@pytest.mark.parametrize(
    "helper,exports",
    (
        (
            "distribution",
            (
                "DistributionInputError",
                "DistributionBin",
                "DescriptiveSummary",
                "linear_quantile",
                "fixed_width_distribution",
                "descriptive_summary",
            ),
        ),
        ("im_basis", ("ResearchInputError", "DailyIMBasis", "daily_im_basis")),
        (
            "price_to_lagged_reference",
            ("LaggedReferenceError", "PriceToLaggedMAObservation", "compute_daily_observations"),
        ),
    ),
)
def test_single_file_helper_imports_keep_their_public_namespace(
    helper: str, exports: tuple[str, ...]
) -> None:
    name = f"market_research.shared.{helper}"
    module = importlib.import_module(name)
    assert module.__file__ is not None
    assert Path(module.__file__).resolve() == (
        RESEARCH_ROOT / "shared" / helper / "src/market_research/shared" / helper / "__init__.py"
    )
    assert not hasattr(module, "__all__")
    for export in exports:
        assert getattr(module, export).__module__ == name
