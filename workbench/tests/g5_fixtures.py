"""Isolated WB-05 harness. Never import this as an operational authorizer."""

import json
import runpy
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_historical_return_g4 import G4, candidate, discovered

from market_research.descriptive import execution

TASK_DIR = Path(__file__).resolve().parents[1] / "tasks" / "historical_return_observation"
G5 = runpy.run_path(str(TASK_DIR / "runtime" / "record_g5.py"))
FIXTURES = runpy.run_path(str(Path(__file__).resolve().parents[2]
                             / "market_research" / "tests" / "observation_fixtures.py"))
DAYS, CODE = FIXTURES["DAYS"], FIXTURES["CODE"]
SERVICES_ACTIVE = ContextVar("wb05_isolated_services_active", default=False)


def frozen_run(root, *, long=False, subjects=None, policy="continue"):
    run_id = discovered(root)
    draft = candidate()
    draft["original_objective"] = "Synthetic WB-05 isolated trailing return observation"
    draft["input_resolution"] = {"kind": "user_interaction",
                                 "reference": "isolated simulated test; no real consent"}
    plan = draft["research_plan"]
    plan.update(subjects=subjects or [CODE], horizons=[21 if long else 2], on_job_failure=policy)
    if not long:
        plan["windows"] = [{"start_date": DAYS[2].isoformat(), "end_date": DAYS[4].isoformat()}]
    assert G4["record_g4"](root, run_id, draft)["result"]["status"] == "PASS"
    return run_id


def authorization(challenge, kind="user_message"):
    return {"source_kind": kind, "source_reference": "isolated deterministic WB-05 fixture",
            "user_statement": (G5["approval_sentence"](challenge) if kind == "user_message" else
                               "SYNTHETIC ONLY: approve this exact challenge for service fakes"),
            "approved_challenge": challenge, "resource_budget": "zero provider calls and charges",
            "data_isolation": "public-service fakes; no network or SQLite or default caches"}


@contextmanager
def isolated_services(*, missing=False, empty=False, long=False):
    from dataclasses import replace
    from datetime import date

    def forbidden(*args, **kwargs):
        raise AssertionError("Provider, network, or default cache access is prohibited")

    sessions = (tuple(date(2009, 12, n) for n in range(1, 32)) + DAYS[:5]) if long else DAYS[:5]
    closes = {day: float(100 + i * 3) for i, day in enumerate(sessions)}
    if missing:
        del closes[DAYS[2]]
    if empty:
        closes = {}
    cal = FIXTURES["CalendarFake"](sessions)
    idx = FIXTURES["IndexFake"](sessions, closes)
    idx.transform = lambda view: replace(view, records=tuple(
        replace(row, index_code=view.scope.index_codes[0],
                symbol=view.scope.index_codes[0].split(".")[0]) for row in view.records))
    with (
        patch("market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
              return_value=cal),
        patch("market_research.descriptive.cases.trailing_return.preparation.create_index_service",
              return_value=idx),
        patch("sqlite3.connect", side_effect=forbidden),
        patch("socket.socket.connect", side_effect=forbidden),
    ):
        token = SERVICES_ACTIVE.set(True)
        try:
            yield cal, idx
        finally:
            SERVICES_ACTIVE.reset(token)


def execute(root, run_id, *, invoke=None, authorize=authorization):
    # Fault injection belongs only to this test harness. Production has no invoke/context seam.
    # A separate namespace keeps observer wrappers free to call the actual public API.
    def controlled(plan):
        if not SERVICES_ACTIVE.get():
            raise AssertionError("Simulated approval requires active isolated service fakes")
        return (invoke or execution.execute_batch)(plan)
    adapter = SimpleNamespace(execute_batch=controlled,
                              preview_plan=execution.preview_plan)
    with patch.dict(G5["record_g5"].__globals__, {"execution": adapter}):
        return G5["record_g5"](root, run_id, authorize=authorize)


def fresh_read(root, run_id):
    import subprocess

    done = subprocess.run([sys.executable, str(TASK_DIR / "runtime" / "record_g5.py"), "--root",
                           str(root),
                           "--run", run_id, "--read"], capture_output=True, text=True, timeout=30)
    assert done.returncode in (0, 1, 2), done.stderr
    return done, json.loads(done.stdout)
