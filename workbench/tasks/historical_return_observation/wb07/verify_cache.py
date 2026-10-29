"""WB-07 public-service reuse audit; deny all Provider/network access."""

import hashlib
import json
import runpy
import socket
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TOOL = runpy.run_path(str(HERE / "acceptance_tool.py"))


def files(root):
    result = {}
    for p in root.iterdir():
        if p.is_file():
            with p.open("rb") as stream:
                result[p.name] = {"sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
                                  "size_bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
    return result


def verify(run_id):
    saved = TOOL["G5"]["read_execution"](TOOL["STORE"], run_id)
    assert saved["status"] == "PASS"
    config = json.loads((TOOL["STORE"] / "wb07-local.json").read_text(encoding="utf-8"))
    cache = Path(config["cache"])
    before = files(cache)
    assert set(before) == {f"{d}.sqlite3" for d in TOOL["DATASETS"]}
    requests, cold_ensures = {}, []
    for job in saved["batch_result"]["job_results"]:
        for attempt in job["input_attempts"]:
            if attempt["ensure_result"] is not None:
                cold_ensures.append({"request": attempt["request"],
                                     "dataset": attempt["final_export"]["dataset"],
                                     "ensure": attempt["ensure_result"]})
        prepared = job["prepared_inputs"]
        for item in [*prepared["calendar_slices"], prepared["index_slice"]]:
            key = json.dumps(item["request"], sort_keys=True)
            if key in requests:
                assert requests[key] == item
            requests[key] = item
    audit, operations, denied = {}, [], []

    def forbidden(*args, **kwargs):
        denied.append("attempt")
        raise AssertionError("Cache audit must not request Provider/network")

    with (TOOL["isolated"](cache, audit),
          patch.object(TOOL["TushareExecutor"], "call", forbidden),
          patch.object(socket.socket, "connect", forbidden)):
        for item in requests.values():
            r = item["request"]
            start, end = (TOOL["date"].fromisoformat(r[k]) for k in ("start_date", "end_date"))
            if "exchange" in r:
                service = TOOL["calendar_service"]()
                request = TOOL["TradeCalendarRange"](r["exchange"], start, end)
            else:
                service = TOOL["index_service"]()
                request = TOOL["IndexDailyRange"](r["index_codes"], start, end)
            coverage = TOOL["public"](service.coverage(request))
            assert coverage["complete"]  # Never invoke Ensure on a non-success target here.
            exported = TOOL["public"](service.export(request))
            assert exported == item["final_export"]
            ensure = TOOL["public"](service.ensure(request))
            assert ensure["already_successful_units"] == ensure["requested_units"]
            assert all(ensure[k] == 0 for k in ("attempted_units", "succeeded_units",
                                               "failed_units", "records_written"))
            assert ensure["complete"]
            assert TOOL["public"](service.export(request)) == exported
            operations.append({"request": r, "coverage": coverage, "ensure": ensure,
                               "export": exported})
    assert not denied
    after = files(cache)
    assert before == after
    return {"run_id": run_id, "result_artifact": saved["result_artifact"],
            "cold_ensures": cold_ensures, "reuse_operations": operations,
            "provider_calls": 0, "network_attempts": 0, "new_records_written": 0,
            "database_files_before": before, "database_files_after": after,
            "database_bytes_hashes_mtimes_unchanged": True, "isolation": audit,
            "verdict": "PASS public-service cache reuse; Research-level warm NOT RUN"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.run)
    TOOL["write"](args.output, result)
    print(json.dumps({"run": args.run, "public_requests_verified": len(result["reuse_operations"]),
                      "provider_calls": 0, "records_written": 0, "verdict": result["verdict"]}))
