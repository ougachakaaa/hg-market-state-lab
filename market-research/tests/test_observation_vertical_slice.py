"""Fresh-process CLI E2E with real DataLake cache and chain durable reuse.

Only test bootstrap accesses internal composition seams. Research production
continues to consume the public Dataset services, with no provider access.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BOOTSTRAP = r"""
import importlib
import json
import sys
from pathlib import Path

# Reuse the owning Dataset's controlled Source fixture; no network/credentials.
sys.path.insert(0, str(Path.cwd() / "data-lake/datasets/tushare_equity_index_options/tests"))
from test_options_runtime import Executor
from data_lake._repository import Repository
from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_trade_calendar as calendar
from data_lake.datasets.tushare_equity_index_options._service import (
    _create_service as option_create,
)
from data_lake.datasets.tushare_equity_index_options._source import DailySource
from data_lake.datasets.tushare_trade_calendar._service import _create_service as calendar_create
from data_lake.datasets.tushare_trade_calendar._source import TradeCalSource

root, mode = Path(sys.argv[1]), sys.argv[2]
lake = root / "datalake"
research = root / "research"

class ControlledExecutor(Executor):
    def call(self, endpoint, **params):
        if mode == "reuse":
            raise AssertionError("repeat invocation accessed Source despite complete cache")
        frame = super().call(endpoint, **params)
        if endpoint == "trade_cal":
            for record in frame.records:
                record["is_open"] = int(record["cal_date"] == "20240102")
        return frame

executor = ControlledExecutor()
source_preparations = []
def source(kind):
    source_preparations.append(kind)
    if mode == "reuse":
        raise AssertionError("repeat invocation prepared Source despite complete DataLake cache")
    return TradeCalSource(executor) if kind == "calendar" else DailySource(executor)

cal = calendar_create(
    Repository(lake / "calendar.sqlite3", "tushare_trade_calendar", "tushare"),
    lambda: source("calendar"),
)
facts = option_create(
    Repository(lake / "options.sqlite3", "tushare_equity_index_options", "tushare"),
    cal, lambda: source("options"),
)
factory_calls, option_calls, calendar_calls, ensure_results = [], [], [], []
# Instrument public operations, leaving their cache/completeness implementation intact.
for operation in ("ensure", "export", "coverage"):
    original = getattr(facts, operation)
    def tracked(request, original=original, operation=operation):
        option_calls.append(operation)
        value = original(request)
        if operation == "ensure":
            ensure_results.append({"attempted": value.attempted_units,
                                   "already_successful": value.already_successful_units,
                                   "complete": value.complete})
        return value
    setattr(facts, operation, tracked)
    original = getattr(cal, operation)
    def tracked_calendar(request, original=original, operation=operation):
        calendar_calls.append(operation)
        return original(request)
    setattr(cal, operation, tracked_calendar)

def options_factory():
    factory_calls.append("options")
    return facts

def calendar_factory():
    factory_calls.append("calendar")
    return cal
options.create_service = options_factory
calendar.create_service = calendar_factory
chain_module = importlib.import_module(
    "market_research.observations.cffex_option_expiry_dte_chain._service"
)
chain_module.owned_path = lambda context, filename: research / filename

from market_research.studies.cffex_option_expiry_dte_collection import cli
if mode == "reuse":
    # Factory construction still occurs; every complete chain must bypass its dependencies.
    original_factory = cli.create_chain_service
    def unavailable():
        raise AssertionError("chain retained hit accessed upstream factory")
    def retained_chain():
        service = original_factory()
        service._options_factory = unavailable
        service._calendar_factory = unavailable
        return service
    cli.create_chain_service = retained_chain
status = cli.main([
    "--product-code", "IO", "--expiry-start-date", "2024-01-02",
    "--expiry-end-date", "2024-02-16", "--target-dte", "18",
])
print(json.dumps({"factories": factory_calls, "options": option_calls,
                  "calendar": calendar_calls, "ensure": ensure_results,
                  "source_preparations": source_preparations,
                  "source_calls": len(executor.calls)}), file=sys.stderr)
raise SystemExit(status)
"""


def retained_payloads(root: Path) -> dict[str, list[tuple[object, ...]]]:
    result = {}
    for path in root.glob("*.sqlite3"):
        with sqlite3.connect(path) as db:
            result[path.name] = db.execute("SELECT * FROM artifacts ORDER BY 1, 2, 3").fetchall()
    return result


def test_cli_vertical_slice_survives_full_process_restart(tmp_path: Path) -> None:
    def invoke(mode: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", BOOTSTRAP, str(tmp_path), mode],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    first = invoke("produce")
    assert first.returncode == 0, first.stderr + first.stdout
    assert "status=success" in first.stdout
    assert "planned_observation_count=2" in first.stdout
    assert "completed_observation_count=2" in first.stdout
    calls = json.loads(first.stderr)
    assert calls["options"] == ["ensure", "export", "export", "export"]
    assert calls["ensure"] == [{"attempted": 1, "already_successful": 0, "complete": True}]
    assert calls["source_calls"] > 0 and calls["source_preparations"]
    persisted = retained_payloads(tmp_path / "research")
    assert set(persisted) == {"cffex_option_expiry_dte_chain.sqlite3"}
    assert len(persisted["cffex_option_expiry_dte_chain.sqlite3"]) == 2
    second = invoke("reuse")
    assert second.returncode == 0, second.stderr + second.stdout
    assert second.stdout == first.stdout
    calls = json.loads(second.stderr)
    assert calls["factories"] == ["options"]
    assert calls["options"] == ["ensure", "export"]
    assert calls["ensure"] == [{"attempted": 0, "already_successful": 1, "complete": True}]
    assert calls["calendar"] == ["export", "export"]  # Options' public prerequisite
    assert calls["source_preparations"] == [] and calls["source_calls"] == 0
    assert retained_payloads(tmp_path / "research") == persisted
    assert {
        path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()
    } == {
        "datalake/calendar.sqlite3",
        "datalake/options.sqlite3",
        "research/cffex_option_expiry_dte_chain.sqlite3",
    }
