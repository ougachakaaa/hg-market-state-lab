"""Explicit WP-A private production and offline verification; never a build input.

Use root Poetry. Business serialization, replay and calculations remain producer-owned.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from datetime import date
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote, urlparse

from fastapi.encoders import jsonable_encoder
from private_mo_examples import checked_file, digest, git, isolation, now, read, require
from private_mo_examples import write as write_json

from market_backtesting.cases.futures_roll_long import (
    FuturesRollRequest,
    build_backtest_result,
    build_evidence_package,
    create_futures_roll_service,
    encode_evidence_package,
    reproduce_futures_roll_evidence,
    validate_backtest_result,
)

REPO = Path(__file__).resolve().parents[2]
START, END = date(2026, 1, 1), date(2026, 11, 11)
PROFILES = ("expiry_to_M1_v1", "expiry_to_Q1_v1")


def write(path, value):
    write_json(path, jsonable_encoder(value))


@contextmanager
def isolated_datasets(root):
    """WP8 pattern: redirect placement only; real public services stay unchanged."""
    calls = read(root / "acquisition.json") if (root / "acquisition.json").exists() else []
    with ExitStack() as stack:
        for dataset, service_name in (
            ("tushare_trade_calendar", "TradeCalendarService"),
            ("tushare_equity_index_futures", "FuturesDailyService"),
            ("tushare_index_daily", "IndexDailyService"),
        ):
            composition = importlib.import_module(f"data_lake.datasets.{dataset}._composition")
            stack.enter_context(patch.object(
                composition, "database_path",
                lambda identity, *_: root / "dataset-cache" / f"{identity}.sqlite3",
            ))
            public = importlib.import_module(f"data_lake.datasets.{dataset}")
            cls = getattr(public, service_name)
            for operation in ("export", "ensure"):
                original = getattr(cls, operation)

                def audited(self, request, *args, _fn=original, _ds=dataset,
                            _op=operation, **kwargs):
                    item = {"dataset": _ds, "operation": _op, "request": asdict(request),
                            "started_at": now()}
                    calls.append(item)
                    try:
                        result = _fn(self, request, *args, **kwargs)
                        item["status"] = "returned"
                        if hasattr(result, "coverage"):
                            item["coverage"] = asdict(result.coverage)
                            item["rows"] = len(result.records)
                        else:
                            item["complete"] = result.complete
                        return result
                    except Exception as exc:
                        item["status"] = type(exc).__name__
                        item["cause_type"] = type(exc.__cause__).__name__
                        raise
                    finally:
                        item["finished_at"] = now()
                        write(root / "acquisition.json", calls)

                stack.enter_context(patch.object(cls, operation, audited))
        # Audit placement without reading or manipulating any Dataset tables.
        original_connect = sqlite3.connect

        def connect(database, *args, **kwargs):
            location = (unquote(urlparse(database).path)
                        if str(database).startswith("file:") else database)
            require(Path(location).resolve().is_relative_to(root / "dataset-cache"),
                    "Dataset connection outside isolated root")
            audit_path = root / "placement-audit.json"
            audit = read(audit_path) if audit_path.exists() else {"connections": 0, "files": []}
            audit["connections"] += 1
            audit["files"] = sorted(set(audit["files"]) | {str(Path(location).resolve())})
            write(audit_path, audit)
            return original_connect(database, *args, **kwargs)

        stack.enter_context(patch.object(sqlite3, "connect", connect))
        yield


@contextmanager
def offline_guard():
    import lab_config

    def forbidden(*args, **kwargs):
        raise AssertionError("offline verification attempted credentials/network/cache")

    with ExitStack() as stack:
        for owner, name in ((lab_config, "tushare_token"), (socket, "create_connection"),
                            (socket.socket, "connect"), (sqlite3, "connect")):
            stack.enter_context(patch.object(owner, name, forbidden))
        yield


def frontend(root, stage):
    completed = subprocess.run(
        ["node", str(REPO / "ui_web/scripts/validate_private_wpa.mjs"), str(root), stage],
        cwd=REPO / "ui_web", text=True, capture_output=True, check=True,
    )
    return json.loads(completed.stdout)


def w2(root):
    output = root / "w2"
    output.mkdir()
    fingerprints = []
    receipts = {}
    service = create_futures_roll_service()
    for profile in PROFILES:
        request = FuturesRollRequest("IM", START, END, profile)
        started = now()
        execution = service.run(request)
        result = build_backtest_result(execution)
        validate_backtest_result(result, execution)
        require(execution.replay.replay.final_portfolio.position is None, "not final flat")
        require(result.daily[-1].position_contract_code is None, "last day not flat")
        require(result.summary.execution_count == 2 + 2 * result.summary.roll_count,
                "execution/roll association")
        rows = {(r.trade_date, r.contract_code): r
                for r in execution.inputs.exports.futures.records}
        for roll in result.rolls:
            old = rows[roll.trade_date, roll.old_contract_code]
            new = rows[roll.trade_date, roll.new_contract_code]
            require(old.delist_date == roll.trade_date and old.close == roll.old_close
                    and new.close == roll.new_close, "roll/source association")
            require(roll.new_slot == ("M1" if "M1" in profile else "Q1"), "roll target")
        for day, record, analyzed in zip(result.daily, execution.replay.replay.daily,
                                         execution.performance.daily, strict=True):
            require(day.daily_pnl == record.transition.daily_pnl
                    and day.daily_return == analyzed.daily_return
                    and day.cumulative_return == analyzed.cumulative_return,
                    "daily accounting association")
        payload = encode_evidence_package(build_evidence_package(execution, result))
        (output / f"{profile}-evidence.json").write_bytes(payload)
        write(output / f"{profile}-result.json", asdict(result))
        write(output / f"{profile}-request.json", asdict(result.request))
        fingerprints.append(result.evidence.input_fingerprint)
        receipts[profile] = {
            "status": "PASS", "started_at": started, "finished_at": now(),
            "fingerprint": fingerprints[-1], "window": asdict(result.window),
            "summary": asdict(result.summary), "coverage": asdict(result.evidence),
            "result_sha256": digest(output / f"{profile}-result.json"),
            "final_flat": True,
        }
        write(output / "acceptance.json", receipts)
    require(len(set(fingerprints)) == 1, "W2 inputs changed between strategies")
    write(output / "frontend-validation.json", frontend(root, "w2"))
    replay = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "replay-w2", "--output", str(root)],
        cwd=REPO, capture_output=True, text=True, check=True,
    )
    write(output / "offline-reproduction.json", json.loads(replay.stdout))


def replay_w2(root):
    results = {}
    with offline_guard():
        for profile in PROFILES:
            payload = checked_file(root, f"w2/{profile}-evidence.json").read_bytes()
            reproduced = reproduce_futures_roll_evidence(payload)
            require(reproduced.status == "verified", "reproduction not verified")
            result = read(checked_file(root, f"w2/{profile}-result.json"))
            require(json.loads(json.dumps(asdict(reproduced.result), default=str)) == result,
                    "retained result differs from official replay")
            require(result["request"] == read(root / "w2" / f"{profile}-request.json"),
                    "request/result mismatch")
            require(result["request"] == {
                "case": "futures_roll_long_v1", "product_code": "IM",
                "start_date": str(START), "end_date": str(END), "strategy_profile": profile,
            }, "wrong fixed request")
            results[profile] = {"status": "PASS", "fingerprint": reproduced.input_fingerprint}
    require(len({r["fingerprint"] for r in results.values()}) == 1, "fingerprint mismatch")
    return {"status": "PASS", "credential_network_sqlite_guard": True, "profiles": results}


def plan():
    from market_research.descriptive.association import AnalysisRequest
    from market_research.descriptive.execution import ResearchPlan
    from market_research.descriptive.observation import DateWindow
    from market_statistics import IntervalCountSpec, QuantileSpec

    return ResearchPlan(
        metric="trailing_cumulative_return_v1", metric_parameters={},
        subjects=["000852.SH"], horizons=[20, 60], windows=[DateWindow(START, END)],
        analysis_requests=[
            AnalysisRequest("quartiles", QuantileSpec([0, .25, .5, .75, 1])),
            AnalysisRequest("distribution", IntervalCountSpec(
                [-.5, -.2, -.1, -.05, 0, .05, .1, .2, .5], "decimal_ratio")),
        ], on_job_failure="continue",
    )


def publication_export(root):
    """Invoke existing Reader and safe read projections, without HTTP/Run simulation."""
    from starlette.requests import Request

    from market_research.descriptive.execution import preview_plan
    from market_research.publication import PublicationStore
    from ui_http.products.research.projection import preview_response
    from ui_http.products.research_publication import endpoint

    reader = PublicationStore(root / "research/publications")
    app = SimpleNamespace(state=SimpleNamespace(publication_store=reader))
    request = Request({"type": "http", "app": app, "query_string": b"", "headers": []})

    def body(response):
        require(response.status_code == 200, "official safe read projection failed")
        return json.loads(response.body)

    listed = reader.list_publications()
    require(len(listed) == 1, "expected one actual publication")
    pid = listed[0]["publication_id"]
    raw = reader.get_publication_manifest(pid)
    expected_scope = preview_response(preview_plan(plan())).model_dump(mode="json")["plan"]
    require(endpoint.manifest(raw)["scope"] == expected_scope, "publication scope mismatch")
    require(listed == [raw] and reader.list_publications(after=pid) == [], "read ordering")
    result = {"pages": [body(endpoint.list_publications(request))],
              "manifests": [body(endpoint.get_manifest(request, pid))["data"]],
              "analyses": [], "views": []}
    for summary in raw["analyses"]:
        aid = summary["analysis_id"]
        require(reader.get_analysis(pid, aid)["summary"] == summary, "analysis association")
        projected = endpoint.project_analysis(reader.get_analysis(pid, aid), pid)
        result["analyses"].append(projected.model_dump(mode="json")["data"])
        for reference in summary["views"]:
            vid = reference["view_id"]
            view = reader.get_chart_view(pid, vid)
            from ui_http.products.research_publication.schemas import ViewResponse

            projected_view = ViewResponse.model_validate({"data": view}).model_dump(mode="json")
            require(projected_view["data"] == view,
                    "ChartView projection changed content")
            result["views"].append({"publication_id": pid, "view_id": vid, "view": view})
    require(result["views"], "no published ChartView")
    return result


def research(root):
    from market_research.descriptive.execution import execute_batch, preview_plan
    from market_research.publication import PublicationStore, publish, retain_source
    from ui_http.products.research.projection import batch_response, preview_response

    output = root / "research"
    output.mkdir()
    preview = preview_plan(plan())
    require((preview.planned_count, preview.analysis_attempt_count) == (2, 4), "wrong expansion")
    write(output / "preview.json", preview_response(preview).model_dump(mode="json"))
    batch = execute_batch(preview.plan)
    # This projection is diagnostic/delivery only. The original Batch is retained below.
    write(output / "batch-summary.json", batch_response(batch).model_dump(mode="json"))
    source = retain_source(batch, "WP-A-real-trailing-return", output / "source.json")
    write(output / "source-reference.json", asdict(source))
    require(any(j.status == "Success" for j in batch.job_results), "no successful research Job")
    pid = publish(batch, source, "WP-A private real market research; public rights BLOCKED",
                  PublicationStore(output / "publications"))
    finish_research(root, expected_pid=pid)


def finish_research(root, expected_pid=None):
    """Finish export of an actual committed publication, without rebuilding a Batch."""
    from market_research.descriptive.capabilities import get_capability, list_capabilities

    output = root / "research"
    exported = publication_export(root)
    pid = exported["manifests"][0]["publication_id"]
    require(expected_pid is None or expected_pid == pid, "wrong published identity")
    write(output / "embedded-publications.json", exported)
    descriptors = list_capabilities()
    write(output / "catalog.json", {
        "list": descriptors, "details": [get_capability(d.id) for d in descriptors],
    })
    write(output / "frontend-validation.json", frontend(root, "research"))
    source = read(output / "source-reference.json")
    batch = read(output / "batch-summary.json")
    write(output / "acceptance.json", {
        "status": "PASS", "batch_status": batch["status"], "publication_id": pid,
        "source_sha256": source["sha256"], "source_bytes": source["size"],
        "jobs": [{"status": j["status"], "horizon": j["fixed_job_spec"]["horizon"]}
                 for j in batch["job_results"]],
        "analyses": len(exported["analyses"]), "views": len(exported["views"]),
        "reader_associations_and_ordering": "PASS",
    })


def file_inventory(root):
    return {
        p.relative_to(root).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in sorted(root.rglob("*")) if p.is_file()
        and p.relative_to(root).parts[0] not in {"dataset-cache", "validation"}
        and p.name not in {"example-index.json", "example-index.sha256"}
    }


def handoff(root, r2, r3):
    require(not (root / "example-index.json").exists(), "index already sealed")
    require(r2 is not None and r3 is not None, "explicit accepted R2/R3 packages required")
    r2, r3 = isolation(r2), isolation(r3)
    # Existing formal tools verify the previous packages; do not rewrite their evidence.
    commands = [
        [sys.executable, str(REPO / "ui_web/scripts/private_mo_examples.py"),
         "verify", "--output", str(r2)],
        [sys.executable, str(REPO / "market_research/scripts/futures_basis_report.py"),
         "verify", str(r3 / "delivery")],
    ]
    for i, command in enumerate(commands, 2):
        result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=True)
        write(root / f"r{i}-verification.json", {"status": "PASS", "stdout": result.stdout})
    for stage in ("w2", "research"):
        require(read(root / f"{stage}-stage.json")["status"] == "PASS", "incomplete stage")
    tooling = root / "tooling"
    tooling.mkdir()
    for name in ("private_wpa_examples.py", "validate_private_wpa.mjs", "private_mo_examples.py"):
        shutil.copyfile(REPO / "ui_web/scripts" / name, tooling / name)
    index = {
        "profile": "wp-a-private-example-index-v1", "revision": 1,
        "classification": "real_market", "publication_rights": "BLOCKED",
        "created_at": now(), "runtime": "runtime.json",
        "delivery_source_revision": git("rev-parse", "HEAD"),
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "examples": {
            **{p: {"request": f"w2/{p}-request.json", "result": f"w2/{p}-result.json",
                   "evidence": f"w2/{p}-evidence.json"} for p in PROFILES},
            "publication": {"reader_export": "research/embedded-publications.json",
                            "store": "research/publications", "source": "research/source.json"},
            "catalog": {"reader_export": "research/catalog.json"},
        },
        "prior_examples": [
            {"identity": "D3-R2-local-20261113-v1", "root": str(r2),
             "manifest": "manifest.json", "sha256": digest(r2 / "manifest.json")},
            {"identity": "D3-R3-local-20261113-v1", "root": str(r3),
             "manifest": "example-index.json", "sha256": digest(r3 / "example-index.json")},
        ],
        "d4": "Consume original Results and safe Reader exports through existing presentations; "
              "preserve coverage, provenance, limitations and origin disclosure. Private only.",
        "files": file_inventory(root),
    }
    write(root / "example-index.json", index)
    (root / "example-index.sha256").write_text(digest(root / "example-index.json") + "\n")
    verify(root)


def verify(root):
    from market_research.descriptive.capabilities import get_capability, list_capabilities

    index_path = checked_file(root, "example-index.json")
    require(digest(index_path) == read_checksum(root), "index checksum mismatch")
    index = read(index_path)
    require(index["profile"] == "wp-a-private-example-index-v1"
            and index["classification"] == "real_market"
            and index["publication_rights"] == "BLOCKED", "index identity/rights")
    require(index["files"] == file_inventory(root), "package inventory mismatch")
    for relative, item in index["files"].items():
        require(digest(checked_file(root, relative)) == item["sha256"], "file digest mismatch")
    for stage in ("w2", "research"):
        require(read(root / f"{stage}-stage.json")["status"] == "PASS", "incomplete stage")
    with offline_guard():
        replay = replay_w2(root)
        require(publication_export(root) == read(root / "research/embedded-publications.json"),
                "Reader export differs from retained data")
        descriptors = list_capabilities()
        require(read(root / "research/catalog.json") == jsonable_encoder({
            "list": descriptors, "details": [get_capability(d.id) for d in descriptors],
        }), "catalog differs from formal capability facade")
        source = read(root / "research/source-reference.json")
        require(digest(checked_file(root, "research/source.json")) == source["sha256"],
                "retained external source digest mismatch")
        for prior in index["prior_examples"]:
            parent = isolation(Path(prior["root"]))
            require(digest(checked_file(parent, prior["manifest"])) == prior["sha256"],
                    "prior example reference changed")
    return {"status": "PASS", "offline_reproduction": replay,
            "frontend": [frontend(root, stage) for stage in ("w2", "research")],
            "files": len(index["files"]), "publication_rights": "BLOCKED"}


def read_checksum(root):
    return checked_file(root, "example-index.sha256").read_text().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=(
        "w2", "research", "export-research", "handoff", "verify", "replay-w2"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--r2", type=Path)
    parser.add_argument("--r3", type=Path)
    args = parser.parse_args()
    root = isolation(args.output)
    if args.operation == "replay-w2":
        print(json.dumps(replay_w2(root)))
        return
    if args.operation in {"w2", "research"}:
        if args.operation == "w2":
            require(not root.exists(), "use a new output directory; no overwrite")
            root.mkdir(mode=0o700, parents=True)
            write(root / "runtime.json", {
                "source_revision": git("rev-parse", "HEAD"), "created_at": now(),
                "python": platform.python_version(),
                "packages": {p: version(p) for p in ("numpy", "pydantic", "tushare")},
                "poetry_lock_sha256": digest(REPO / "poetry.lock"),
                "npm_lock_sha256": digest(REPO / "ui_web/package-lock.json"),
                "tool_sha256": digest(Path(__file__).resolve()),
                "producer_worktree_clean": not git("diff", "HEAD", "--", "market_backtesting",
                                                   "market_research", "data_lake", "config"),
            })
        require(root.is_dir() and (root / "runtime.json").is_file(), "missing package runtime")
        require(root.stat().st_mode & 0o077 == 0, "private output must be owner-only")
        require(not (root / args.operation).exists(), "stage already exists; no overwrite")
        receipt = root / f"{args.operation}-stage.json"
        write(receipt, {"status": "RUNNING", "started_at": now()})
        try:
            with isolated_datasets(root):
                (w2 if args.operation == "w2" else research)(root)
            write(receipt, {"status": "PASS", "finished_at": now()})
        except Exception as exc:
            write(receipt, {"status": "FAIL", "exception_type": type(exc).__name__,
                            "finished_at": now()})
            raise
    elif args.operation == "export-research":
        require(not (root / "example-index.json").exists(), "sealed package is immutable")
        require(not (root / "research/acceptance.json").exists(), "stage already accepted")
        receipt = root / "research-stage.json"
        write(receipt, {"status": "RUNNING", "operation": "offline_export", "started_at": now()})
        try:
            with offline_guard():
                finish_research(root)
            write(receipt, {"status": "PASS", "operation": "offline_export", "finished_at": now()})
        except Exception as exc:
            write(receipt, {"status": "FAIL", "exception_type": type(exc).__name__})
            raise
    elif args.operation == "handoff":
        handoff(root, args.r2, args.r3)
    else:
        print(json.dumps(verify(root)))


if __name__ == "__main__":
    main()
