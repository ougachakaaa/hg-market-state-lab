"""WB-07 opt-in operational controls; no standalone live authorization surface.

Use prepare() without Source I/O. A trusted session host may call execute() only
after resolving the real user's exact G5 challenge approval. Never load consent
from a file. Private imports configure/audit storage, never obtain research facts.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import socket
import sqlite3
import tempfile
import threading
import time
from collections import Counter
from contextlib import ExitStack, closing, contextmanager
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from data_lake import OperationError
from data_lake.adapters.outbound.sqlite import Repository
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_index_daily import _composition as ic
from data_lake.datasets.tushare_index_daily import create_service as index_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import _composition as cc
from data_lake.datasets.tushare_trade_calendar import create_service as calendar_service
from data_lake.providers.tushare import TushareExecutor
from data_lake.providers.tushare._executor import request_interval, resolve_credential

ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "workbench/tasks/historical_return_observation"
G5 = runpy.run_path(str(TASK / "runtime" / "record_g5.py"))
STORE = ROOT / "workbench/.runs"
DATASETS = ("tushare_trade_calendar", "tushare_index_daily")
SUBJECTS = ("000852.SH", "000905.SH", "000300.SH", "000016.SH")
LIMITS = {"provider_calls": 160, "calls_per_minute": 60, "wall_seconds": 900,
          "database_bytes": 512 * 1024**2, "evidence_bytes": 256 * 1024**2}


def write(path, value):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def size(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def default_state():
    result = {}
    for dataset in DATASETS:
        for p in (ROOT / "data_lake/datasets" / dataset / "data").glob("*"):
            if p.is_file():
                stat = p.stat()
                with p.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                result[str(p.relative_to(ROOT))] = {
                    "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                    "sha256": digest}
    return result


def target_path(database):
    value = os.fspath(database)
    if value.startswith("file:"):
        value = unquote(urlsplit(value).path)
        if os.name == "nt" and value.startswith("/"):
            value = value[1:]
    return Path(value).resolve()


@contextmanager
def isolated(root, audit):
    """Persistent extension of LIVE-E2E-01's checked composition mechanism."""
    root = root.resolve()
    if ROOT == root or ROOT in root.parents or not root.is_dir():
        raise ValueError("External isolated directory required")
    paths = {d: root / f"{d}.sqlite3" for d in DATASETS}
    original_init, original_connect = Repository.__init__, sqlite3.connect
    bindings, connections = Counter(), Counter()
    before = default_state()

    def location(dataset, storage_root):
        return paths[dataset]

    def checked_init(self, path, dataset, source):
        if dataset not in paths or Path(path).resolve() != paths[dataset]:
            raise ValueError("Repository isolation escape")
        bindings[dataset] += 1
        original_init(self, path, dataset, source)

    def checked_connect(database, *args, **kwargs):
        target = target_path(database)
        if target not in paths.values():
            raise ValueError("SQLite isolation escape")
        connections[target.name] += 1
        return original_connect(database, *args, **kwargs)

    with ExitStack() as stack:
        stack.enter_context(patch.object(cc, "database_path", location))
        stack.enter_context(patch.object(ic, "database_path", location))
        stack.enter_context(patch.object(Repository, "__init__", checked_init))
        stack.enter_context(patch.object(sqlite3, "connect", checked_connect))
        cal, idx = calendar_service(), index_service()
        assert cal._core._repository.path == paths[DATASETS[0]]
        assert idx._repository.path == paths[DATASETS[1]]
        assert idx._calendar._core._repository.path == paths[DATASETS[0]]
        audit.update(factory_bindings_verified=True, implicit_calendar_verified=True)
        try:
            yield
        finally:
            audit.update(repository_bindings=dict(bindings), sqlite_connections=dict(connections),
                         default_cache_unchanged=before == default_state())
            if not audit["default_cache_unchanged"]:
                raise ValueError("Default cache changed")


def public(value):
    return G5["OUTPUT"]["public_value"](value)


def probe_defaults():
    """Public compatibility probes; deny any writable connection or Source socket."""
    before = default_state()
    original = sqlite3.connect
    connections = []

    def checked(database, *args, **kwargs):
        if not kwargs.get("uri") or "mode=ro" not in os.fspath(database):
            raise AssertionError("Default probe attempted writable SQLite")
        connections.append(target_path(database).name)
        return original(database, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("Preflight attempted network")

    report = {}
    with (patch.object(sqlite3, "connect", checked),
          patch.object(socket.socket, "connect", forbidden)):
        for dataset, service, request in (
            (DATASETS[0], calendar_service(), TradeCalendarRange("SSE", date(2026, 1, 1),
                                                                date(2026, 10, 29))),
            (DATASETS[1], index_service(), IndexDailyRange(SUBJECTS, date(2026, 1, 1),
                                                          date(2026, 10, 29))),
        ):
            try:
                report[dataset] = {"coverage": public(service.coverage(request))}
            except OperationError as exc:
                report[dataset] = {"status": "OperationError",
                                   "requires_rebuild": "rebuild" in str(exc).lower(),
                                   "calendar_dependency": "calendar" in str(exc).lower()}
        try:
            credential = resolve_credential()
            report["credential_available"] = bool(credential.strip())
            del credential
        except OperationError:
            report["credential_available"] = False
    report.update(readonly_connections=connections,
                  default_cache_unchanged=before == default_state(),
                  provider_calls=0, permissions="not_verified", metadata="not_verified")
    assert report["default_cache_unchanged"]
    return report


def prepare(run_id):
    frozen = G5["G4"]["read_frozen"](STORE, run_id)
    assert frozen["preview"]["planned_count"] == 16
    assert frozen["preview"]["analysis_attempt_count"] == 32
    config_path = STORE / "wb07-local.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config["cold_run"] != run_id:
            raise ValueError("Existing cold configuration requires explicit reconciliation")
        cache = Path(config["cache"])
        if any(cache.iterdir()):
            raise ValueError("Retained cache is nonempty; inspect it, never reset preparation")
    else:
        cache = Path(tempfile.mkdtemp(prefix="wb07-cache-"))
    audit = {}
    with isolated(cache, audit):
        assert not any(cache.iterdir())
        initial = public(calendar_service().coverage(
            TradeCalendarRange("SSE", date(2026, 1, 1), date(2026, 10, 29))))
        try:
            index_initial = public(index_service().coverage(
                IndexDailyRange(SUBJECTS, date(2026, 1, 1), date(2026, 10, 29))))
        except OperationError:
            index_initial = {"status": "OperationError",
                             "prerequisite": "incomplete Calendar; target units unknown"}
        # Absence is tested with a real read-only connection against a disposable
        # empty file, never by creating synthetic market facts.
        test_db = cache / f"{DATASETS[0]}.sqlite3"
        test_db.touch()
        with closing(sqlite3.connect(test_db.as_uri() + "?mode=ro", uri=True)) as connection:
            connection.execute("PRAGMA query_only=ON")
        test_db.unlink()
    defaults = probe_defaults()
    report = {"run_id": run_id, "workflow": frozen["workflow_artifact"],
              "preview": frozen["preview_artifact"], "initial_calendar_coverage": initial,
              "initial_index_coverage": index_initial,
              "isolation": audit, "defaults": defaults, "limits": LIMITS,
              "execution": "NOT RUN; exact user authorization and tested controls required",
              "approval_sentence": G5["approval_sentence"](G5["challenge_for"](frozen))}
    # Private runtime configuration remains ignored. It carries no consent.
    write(STORE / "wb07-local.json", {"cache": str(cache), "cold_run": run_id})
    write(STORE / "wb07-preflight.json", report)
    return report


@contextmanager
def controls(cache, run_id, audit):
    """Enforce call ceiling and a process deadline; never retry after termination."""
    started, calls = time.monotonic(), Counter()
    lock = threading.Lock()
    original = TushareExecutor.call
    baseline = size(STORE / run_id)
    stopped = threading.Event()
    journal = STORE / f"wb07-audit-{run_id}.json"

    def snapshot():
        audit.update(provider_calls=dict(calls), elapsed_seconds=time.monotonic() - started,
                     database_bytes=size(cache), new_evidence_bytes=size(STORE / run_id) - baseline)
        write(journal, audit)

    def check():
        if time.monotonic() - started >= LIMITS["wall_seconds"]:
            return "wall_time"
        if size(cache) > LIMITS["database_bytes"]:
            return "database_storage"
        if size(STORE / run_id) - baseline > LIMITS["evidence_bytes"]:
            return "evidence_storage"
        return None

    def watchdog():
        while not stopped.wait(0.25):
            try:
                with lock:
                    failure = check()
                    if failure:
                        audit.update(terminated=failure, execution_state="uncertain_no_retry")
                        try:
                            snapshot()
                        finally:
                            os._exit(124)
            except Exception:
                # A lost monitoring/audit facility cannot leave acquisition running.
                # Never serialize exception text or let a failed snapshot prevent exit.
                try:
                    audit.update(terminated="control_failure",
                                 execution_state="uncertain_no_retry")
                    snapshot()
                finally:
                    os._exit(124)

    def bounded(self, endpoint, **parameters):
        with lock:
            if sum(calls.values()) >= LIMITS["provider_calls"] or check():
                audit["ceiling_reached"] = True
                snapshot()
                raise OperationError("WB-07 operational ceiling reached; no retry")
            if endpoint not in {"trade_cal", "index_basic", "index_daily"}:
                raise OperationError("Unexpected acceptance endpoint")
            calls[endpoint] += 1
            snapshot()  # Durable before crossing the actual provider boundary.
        return original(self, endpoint, **parameters)

    thread = threading.Thread(target=watchdog, daemon=True)
    with patch.dict(os.environ, {"TUSHARE_CALLS_PER_MINUTE": str(LIMITS["calls_per_minute"])}), \
            patch.object(TushareExecutor, "call", bounded):
        assert 60 / request_interval() == LIMITS["calls_per_minute"]
        thread.start()
        try:
            yield
        finally:
            stopped.set()
            thread.join()
            snapshot()


def execute(run_id, authorize):
    """Trusted host supplies actual session consent callback, never file-based consent."""
    config = json.loads((STORE / "wb07-local.json").read_text(encoding="utf-8"))
    cache = Path(config["cache"])
    audit = {"limits": LIMITS, "run_id": run_id,
             "storage_enforcement": "250ms sampled; may overshoot by in-flight writes"}
    # Validate intent before entering controls; the ordinary adapter also checks it.
    state = G5["RunStore"](STORE).read(run_id)
    if G5["intents"](state):
        raise ValueError("Existing intent: inspect original evidence; no retry")
    with isolated(cache, audit), controls(cache, run_id, audit):
        result = G5["record_g5"](STORE, run_id, authorize=authorize)
    write(STORE / f"wb07-audit-{run_id}.json", audit)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WB-07 no-Source readiness only")
    parser.add_argument("--prepare-run", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.prepare_run), ensure_ascii=True, indent=2))
