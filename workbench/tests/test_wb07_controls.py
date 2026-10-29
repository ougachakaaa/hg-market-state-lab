"""No-Source safety tests for the explicitly commissioned WB-07 acceptance tool."""

import json
import runpy
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from data_lake import OperationError
from data_lake.providers.tushare import TushareExecutor

TOOL = Path(__file__).resolve().parents[1] / (
    "tasks/historical_return_observation/wb07/acceptance_tool.py")


def load():
    return runpy.run_path(str(TOOL))


def test_persistent_storage_and_escape_guards():
    module = load()
    with TemporaryDirectory(prefix="wb07-control-test-") as directory:
        root = Path(directory)
        audit = {}
        before = module["default_state"]()
        with module["isolated"](root, audit):
            with closing(sqlite3.connect(root / "tushare_index_daily.sqlite3")) as db:
                db.execute("CREATE TABLE operational_probe (value INTEGER)")
                db.execute("INSERT INTO operational_probe VALUES (7)")
                db.commit()
            with pytest.raises(ValueError, match="isolation escape"):
                sqlite3.connect(root / "forbidden.sqlite3")
        with module["isolated"](root, audit):
            with closing(sqlite3.connect(root / "tushare_index_daily.sqlite3")) as db:
                assert db.execute("SELECT value FROM operational_probe").fetchone() == (7,)
        assert module["default_state"]() == before
        assert audit["implicit_calendar_verified"] and audit["default_cache_unchanged"]


def test_call_ceiling_and_endpoint_deny_without_source(tmp_path):
    module = load()
    store = tmp_path / "evidence"
    run = store / "test"
    run.mkdir(parents=True)
    cache = tmp_path / "cache"
    cache.mkdir()
    controls_globals = module["controls"].__wrapped__.__globals__
    calls = []

    def fake(self, endpoint, **parameters):
        calls.append(endpoint)
        return "test response"

    with (patch.dict(controls_globals, STORE=store),
          patch.dict(module["LIMITS"], provider_calls=2),
          patch.object(TushareExecutor, "call", fake)):
        audit = {}
        with module["controls"](cache, "test", audit):
            client = TushareExecutor()
            with pytest.raises(OperationError, match="Unexpected"):
                client.call("other_endpoint")
            assert client.call("trade_cal") == "test response"
            assert client.call("index_daily") == "test response"
            with pytest.raises(OperationError, match="ceiling"):
                client.call("trade_cal")
        assert calls == ["trade_cal", "index_daily"]
        assert audit["provider_calls"] == {"trade_cal": 1, "index_daily": 1}
        assert json.loads((store / "wb07-audit-test.json").read_text())["ceiling_reached"]


@pytest.mark.parametrize("kind", ["wall_seconds", "database_bytes", "evidence_bytes",
                                 "monitor_failure", "audit_failure"])
def test_watchdog_hard_termination_without_source(tmp_path, kind):
    store, cache = tmp_path / "store", tmp_path / "cache"
    (store / "test").mkdir(parents=True)
    cache.mkdir()
    script = """
import runpy, sys, time
from pathlib import Path
m = runpy.run_path(sys.argv[1])
g = m['controls'].__wrapped__.__globals__
g['STORE'] = Path(sys.argv[2])
kind = sys.argv[4]
m['LIMITS'][kind] = 0.05 if kind == 'wall_seconds' else 1
with m['controls'](Path(sys.argv[3]), 'test', {}):
    if kind == 'monitor_failure':
        def broken_size(root):
            raise OSError('simulated lost monitor')
        g['size'] = broken_size
    if kind == 'audit_failure':
        def broken_write(path, value):
            raise OSError('simulated lost audit')
        g['write'] = broken_write
        m['LIMITS']['wall_seconds'] = 0.05
    if kind == 'database_bytes':
        (Path(sys.argv[3]) / 'probe').write_bytes(b'123')
    if kind == 'evidence_bytes':
        (Path(sys.argv[2]) / 'test/probe').write_bytes(b'123')
    time.sleep(5)
raise AssertionError('watchdog did not terminate')
"""
    result = subprocess.run([sys.executable, "-c", script, str(TOOL), str(store),
                             str(cache), kind], capture_output=True, timeout=15)
    assert result.returncode == 124, result.stderr.decode()
    if kind in {'monitor_failure', 'audit_failure'}:
        return  # Exit must still occur when the audit itself cannot be written.
    audit = json.loads((store / "wb07-audit-test.json").read_text())
    assert audit["execution_state"] == "uncertain_no_retry"
    assert audit["provider_calls"] == {}
