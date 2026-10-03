"""Shared resolver ownership, public dependency and lifecycle boundaries."""

import ast
import importlib.util
import re
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from data_lake.datasets import tushare_equity_index_options as options
from market_research.observations import ObservationError
from market_research.shared import cffex_option_expiry_universe as universe
from observation_support import OptionsDouble, row

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "market-research/shared/cffex_option_expiry_universe/src"
    / "market_research/shared/cffex_option_expiry_universe"
)


def test_component_authority_is_reachable_and_source_points_to_its_owner() -> None:
    navigation = (
        ROOT / "ARCHITECTURE.md",
        ROOT / "market-research/ARCHITECTURE.md",
        ROOT / "market-research/shared/ARCHITECTURE.md",
        SOURCE.parents[3] / "ARCHITECTURE.md",
    )
    for current, target in zip(navigation, navigation[1:], strict=False):
        links = {
            (current.parent / raw.split("#", 1)[0]).resolve()
            for raw in re.findall(r"\]\(([^)]+)\)", current.read_text(encoding="utf-8"))
        }
        assert target.resolve() in links
    entry = navigation[-1]
    for name in ("CONTRACT.md", "IMPLEMENTATION.md"):
        assert (entry.parent / name).is_file()
        assert f"({name})" in entry.read_text(encoding="utf-8")
    docstring = ast.get_docstring(ast.parse((SOURCE / "__init__.py").read_text(encoding="utf-8")))
    assert "Canonical authority: ../../../../ARCHITECTURE.md (owner root)" in (docstring or "")
    assert "Public Python mapping: ../../../../IMPLEMENTATION.md (owner root)" in (docstring or "")


def test_resolver_is_a_shared_component_with_its_own_public_failure_boundary() -> None:
    old = importlib.util.find_spec("market_research.observations.cffex_option_expiry_universe")
    # An ignored pycache directory may remain after a checkout; it is not a public package.
    assert old is None or old.origin is None
    assert not hasattr(universe, "ExpiryUniverseArtifact")
    assert not hasattr(universe, "create_service")
    assert not hasattr(universe, "__all__")
    for error in (
        universe.ExpiryUniverseInvalidRequestError,
        universe.ExpiryUniverseOperationError,
    ):
        assert issubclass(error, universe.ExpiryUniverseError)
        assert not issubclass(error, ObservationError)
    resolver = universe.create_resolver()
    assert callable(resolver.resolve) and not hasattr(resolver, "ensure")


def test_resolver_only_imports_options_public_facts_and_has_no_research_lifecycle() -> None:
    allowed = {"data_lake", "data_lake.datasets", "data_lake.datasets.tushare_equity_index_options"}
    for path in SOURCE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                assert name.split(".")[0] not in {
                    "sqlite3",
                    "pathlib",
                    "tushare",
                    "market_snapshot",
                    "backend_api",
                    "lab",
                }
                assert not name.startswith(
                    ("market_research.observations", "market_research.studies")
                )
                assert not name.startswith("data_lake") or name in allowed
            if isinstance(node, ast.ImportFrom) and node.level:
                assert node.level == 1
        assert "observations/" not in path.read_text(encoding="utf-8")


def test_public_resolver_repeated_calls_project_owned_values_without_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An unrelated corrupt legacy file must neither be read nor altered.
    legacy = tmp_path / "cffex_option_expiry_universe.sqlite3"
    legacy.write_bytes(b"old state must be ignored")
    monkeypatch.chdir(tmp_path)
    day = date(2025, 10, 9)
    expiry = date(2025, 10, 23)
    facts = OptionsDouble((day,), (row(expiry, day),))
    factory_calls = []

    def factory() -> options.OptionsDailyService:
        from typing import cast

        factory_calls.append(True)
        return cast(options.OptionsDailyService, facts)

    monkeypatch.setattr(options, "create_service", factory)
    request = universe.ExpiryUniverseRequest("MO", day, expiry)
    first = universe.create_resolver().resolve(request)
    second = universe.create_resolver().resolve(request)
    assert first == second and factory_calls == [True, True]
    assert [op for op, _ in facts.calls] == ["ensure", "export"] * 2
    assert first.expiries == (expiry,)
    assert not any(
        hasattr(first, name)
        for name in ("observation_identity", "semantic_identity", "rows", "path")
    )
    for value in (
        first,
        first.provenance,
        first.provenance.scope,
        first.provenance.window,
        first.provenance.coverage,
    ):
        assert type(value).__module__.startswith(universe.__name__)
    with pytest.raises(FrozenInstanceError):
        first.provenance.coverage.complete = False  # type: ignore[misc]
    assert list(tmp_path.iterdir()) == [legacy]
    assert legacy.read_bytes() == b"old state must be ignored"


def test_invalid_resolve_and_future_window_precede_all_upstream_factories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden() -> options.OptionsDailyService:
        pytest.fail("invalid resolver input accessed upstream")

    monkeypatch.setattr(options, "create_service", forbidden)
    resolver = universe.create_resolver()
    from typing import Any, cast

    with pytest.raises(universe.ExpiryUniverseInvalidRequestError):
        resolver.resolve(cast(Any, object()))
    with pytest.raises(universe.ExpiryUniverseInvalidRequestError, match="Asia/Shanghai"):
        universe.ExpiryUniverseRequest("MO", date(2025, 1, 1), date.max)


def test_resolver_interruption_propagates_without_success() -> None:
    def interrupt() -> options.OptionsDailyService:
        raise KeyboardInterrupt

    resolver = universe.ExpiryUniverseResolver(_options_factory=interrupt)
    with pytest.raises(KeyboardInterrupt):
        resolver.resolve(universe.ExpiryUniverseRequest("MO", date(2025, 1, 1), date(2025, 1, 2)))


def test_resolver_factory_maps_construction_failure_to_its_own_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typing import Any

    from market_research.shared.cffex_option_expiry_universe import _service

    def fail(**kwargs: Any) -> Any:
        raise OSError("controlled construction failure")

    monkeypatch.setattr(_service, "ExpiryUniverseResolver", fail)
    with pytest.raises(universe.ExpiryUniverseOperationError, match="construction failed"):
        universe.create_resolver()
