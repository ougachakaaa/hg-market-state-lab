"""Observation public topology, ownership and repository dependency directions."""

import ast
import importlib
import subprocess
from pathlib import Path

import pytest

from market_research.observations import cffex_option_expiry_dte_chain as chain
from observation_support import CalendarDouble, OptionsDouble, row

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "market-research/src/market_research/observations"


def test_observations_only_import_selected_public_datalake_boundaries() -> None:
    allowed = {
        "data_lake",
        "data_lake.datasets",
        "data_lake.datasets.tushare_equity_index_options",
        "data_lake.datasets.tushare_trade_calendar",
    }
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom) and not node.level
                else []
            )
            for name in names:
                assert name.split(".")[0] not in {
                    "tushare",
                    "market_snapshot",
                    "backend_api",
                    "lab",
                }
                if name.startswith("data_lake"):
                    assert name in allowed, (path, name)
        if path.parent == SOURCE:
            assert not any(
                isinstance(node, ast.ImportFrom) and (node.module or "").startswith("data_lake")
                for node in ast.walk(tree)
            ), path


def test_every_runtime_sqlite_sidecar_is_ignored() -> None:
    paths = [
        f"market-research/observations/{identity}/data/{identity}.sqlite3{suffix}"
        for identity in ("cffex_option_expiry_universe", "cffex_option_expiry_dte_chain")
        for suffix in ("", "-wal", "-shm", "-journal")
    ]
    result = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        input=("\0".join(paths) + "\0").encode(),
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode().rstrip("\0").split("\0") == paths


def test_public_factory_ensure_is_durable_and_cwd_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import date

    expiry, trade = date(2025, 10, 23), date(2025, 10, 9)
    facts, dates = OptionsDouble((trade,), (row(expiry, trade),)), CalendarDouble((trade,))
    from data_lake.datasets import tushare_equity_index_options as options
    from data_lake.datasets import tushare_trade_calendar as calendar
    from market_research.observations._sqlite import owned_path

    monkeypatch.chdir(tmp_path)
    assert owned_path("market-research/observations/example", "example.sqlite3") == (
        ROOT / "market-research/observations/example/data/example.sqlite3"
    )
    monkeypatch.setattr(options, "create_service", lambda: facts)
    monkeypatch.setattr(calendar, "create_service", lambda: dates)
    internal = importlib.import_module(
        "market_research.observations.cffex_option_expiry_dte_chain._service"
    )
    path = tmp_path / "chain.sqlite3"
    monkeypatch.setattr(internal, "owned_path", lambda context, filename: path)
    request = chain.ExpiryDteChainRequest("MO", expiry, 15)
    artifact = chain.create_service().ensure(request)
    assert path.exists() and artifact.complete
    monkeypatch.setattr(
        options, "create_service", lambda: (_ for _ in ()).throw(AssertionError("upstream"))
    )
    monkeypatch.setattr(
        calendar, "create_service", lambda: (_ for _ in ()).throw(AssertionError("upstream"))
    )
    assert chain.create_service().ensure(request) == artifact
