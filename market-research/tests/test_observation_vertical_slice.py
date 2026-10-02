"""Fresh-process controlled Study CLI E2E with durable producer reuse."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Test-only bootstrap patches internal persistence composition and the public
# Dataset factories. The production CLI retains its four semantic inputs.
BOOTSTRAP = r"""
import importlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "market-research/tests"))
from observation_support import CalendarDouble, OptionsDouble, row
from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_trade_calendar as calendar

root = Path(sys.argv[1])
mode = sys.argv[2]
first, second = date(2025, 10, 23), date(2025, 11, 20)
dates = (date(2025, 9, 24), date(2025, 10, 1), date(2025, 10, 22))
facts = OptionsDouble(dates, (
    row(first, dates[0]), row(first, dates[1]), row(second, dates[2]),
))
cal = CalendarDouble(dates)
factory_calls = []
def options_factory():
    factory_calls.append("options")
    if mode == "reuse":
        raise AssertionError("retained hit accessed upstream factory")
    return facts
def calendar_factory():
    factory_calls.append("calendar")
    if mode == "reuse":
        raise AssertionError("retained hit accessed upstream factory")
    return cal
options.create_service = options_factory
calendar.create_service = calendar_factory
for identity in ("cffex_option_expiry_universe", "cffex_option_expiry_dte_chain"):
    module = importlib.import_module(f"market_research.observations.{identity}._service")
    module.owned_path = lambda context, filename: root / filename

from market_research.studies.cffex_option_expiry_dte_collection.cli import main
status = main([
    "--product-code", "MO", "--expiry-start-date", "2025-10-01",
    "--expiry-end-date", "2025-11-30", "--target-dte", "30",
])
print(json.dumps({"factories": factory_calls, "options": len(facts.calls),
                  "calendar": len(cal.calls)}), file=sys.stderr)
raise SystemExit(status)
"""


def retained_payloads(root: Path) -> dict[str, list[tuple[object, ...]]]:
    result = {}
    for path in root.glob("*.sqlite3"):
        with sqlite3.connect(path) as db:
            result[path.name] = db.execute("SELECT * FROM artifacts ORDER BY 1, 2, 3").fetchall()
    return result


def test_cli_vertical_slice_survives_full_process_restart(tmp_path: Path) -> None:
    first = subprocess.run(
        [sys.executable, "-c", BOOTSTRAP, str(tmp_path), "produce"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stderr
    assert "status=success" in first.stdout
    assert "planned_observation_count=2" in first.stdout
    assert "completed_observation_count=2" in first.stdout
    calls = json.loads(first.stderr)
    assert calls["factories"] and calls["options"] == 4 and calls["calendar"] == 2
    persisted = retained_payloads(tmp_path)
    assert len(persisted["cffex_option_expiry_universe.sqlite3"]) == 1
    assert len(persisted["cffex_option_expiry_dte_chain.sqlite3"]) == 2
    second = subprocess.run(
        [sys.executable, "-c", BOOTSTRAP, str(tmp_path), "reuse"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert second.returncode == 0, second.stderr
    assert second.stdout == first.stdout
    assert json.loads(second.stderr) == {"factories": [], "options": 0, "calendar": 0}
    assert retained_payloads(tmp_path) == persisted
    assert {path.name for path in tmp_path.iterdir()} == {
        "cffex_option_expiry_universe.sqlite3",
        "cffex_option_expiry_dte_chain.sqlite3",
    }
