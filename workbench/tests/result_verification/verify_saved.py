"""WB-07 independent oracle over immutable saved public Exports; no market I/O."""

import base64
import hashlib
import json
import runpy
import socket
import sqlite3
from datetime import date
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TOOL = runpy.run_path(str(HERE / "acceptance_tool.py"))
NAMES = dict(zip(TOOL["SUBJECTS"], ("中证1000", "中证500", "沪深300", "上证50"), strict=True))
COVERAGE = ("requested_units", "successful_units", "missing_units", "pending_units",
            "failed_units", "complete")
FLOATS = ("open", "high", "low", "close", "pre_close", "change", "pct_change", "volume", "amount")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def envelope(view, dataset, request, count):
    assert view["dataset"] == dataset and view["export_schema_version"] == 1
    assert view["view"] == ("calendar" if "calendar" in dataset else "index_daily")
    assert view["window"] == {k: request[k] for k in ("start_date", "end_date")}
    c = view["coverage"]
    assert all(type(c[k]) is int and c[k] >= 0 for k in COVERAGE[:-1])
    assert c["requested_units"] == count
    assert sum(c[k] for k in COVERAGE[1:-1]) == count
    assert c["complete"] == (c["successful_units"] == count)
    assert len(view["records"]) == c["successful_units"]
    assert c["complete"]  # This saved cold result has complete inputs.


def verify_job(job, requests):
    fixed, obs = job["fixed_job_spec"], job["observation_set"]
    code, h, window = fixed["subject"], fixed["horizon"], fixed["historical_sample_window"]
    assert window == {"start_date": "2026-01-01", "end_date": "2026-10-29"}
    assert fixed["metric"] == "trailing_cumulative_return_v1" and fixed["metric_parameters"] == {}
    assert job["status"] == "Success" and not job["failures"]
    identity = [fixed["metric"], code, [], h, "trading_sessions", window["start_date"],
                window["end_date"], "end_session", "inclusive"]
    assert job["job_identity"] == obs["job_identity"] == identity
    prepared, days, calendar_payload = job["prepared_inputs"], {}, []
    for item in prepared["calendar_slices"]:
        req, view = item["request"], item["final_export"]
        start, end = (date.fromisoformat(req[k]) for k in ("start_date", "end_date"))
        count = (end - start).days + 1
        envelope(view, "tushare_trade_calendar", req, count)
        assert view["scope"] == {"exchange": "SSE"}
        assert [date.fromisoformat(r["cal_date"]).toordinal() for r in view["records"]] == (
            list(range(start.toordinal(), end.toordinal() + 1)))
        for row in view["records"]:
            assert row["exchange"] == "SSE" and type(row["is_open"]) is int
            assert row["is_open"] in (0, 1)
            assert row["cal_date"] not in days or days[row["cal_date"]] == row
            days[row["cal_date"]] = row
        calendar_payload.append([view["dataset"], view["view"], 1, "SSE", req["start_date"],
                                 req["end_date"], [view["coverage"][k] for k in COVERAGE],
                                 [[r[k] for k in ("exchange", "cal_date", "is_open",
                                                 "pretrade_date")] for r in view["records"]]])
    opens = sorted(d for d, row in days.items() if row["is_open"] == 1)
    anchors = [d for d in opens if window["start_date"] <= d <= window["end_date"]]
    assert obs["candidate_anchors"] == anchors and anchors[-1] == "2026-10-29"
    first = opens.index(anchors[0]) - h
    assert first >= 0
    sessions = opens[first:opens.index(anchors[-1]) + 1]
    item = prepared["index_slice"]
    req, view = item["request"], item["final_export"]
    assert req == {"index_codes": [code], "start_date": sessions[0], "end_date": sessions[-1]}
    envelope(view, "tushare_index_daily", req, len(sessions))
    assert view["scope"] == {"index_codes": [code]}
    assert [r["trade_date"] for r in view["records"]] == sessions
    rows = {r["trade_date"]: r for r in view["records"]}
    metadata = {(r["index_code"], r["symbol"], r["name"], r["market"], r["publisher"],
                 r["category"]) for r in rows.values()}
    assert len(metadata) == 1
    meta = next(iter(metadata))
    assert meta[:3] == (code, code[:6], NAMES[code])
    endpoints = [[a, [code, a], [code, opens[opens.index(a) - h]], []] for a in anchors]
    values = [rows[a]["close"] / rows[back[1]]["close"] - 1 for a, _, back, _ in endpoints]
    assert all(rows[a]["close"] > 0 and rows[back[1]]["close"] > 0
               for a, _, back, _ in endpoints)
    assert [v.hex() for v in values] == [o["scalar_value"].hex()
                                       for o in obs["eligible_observations"]]
    keys = [[identity, a] for a in anchors]
    assert [o["observation_key"] for o in obs["eligible_observations"]] == keys
    assert [o["anchor"] for o in obs["eligible_observations"]] == anchors
    assert (obs["candidate_count"], obs["eligible_count"], obs["unavailable_count"],
            obs["excluded_count"]) == (len(anchors), len(values), 0, 0)
    assert not obs["unavailable_observations"] and not obs["excluded_observations"]
    assert (obs["observation_coverage"], obs["unavailable_ratio"],
            obs["excluded_ratio"]) == (1, 0, 0)
    for part, dates in (("overall", sessions), ("sample", anchors),
                        ("warm_up", [d for d in sessions if d < anchors[0]])):
        c = obs["market_fact_coverage"][part]
        assert c["expected_keys"] == c["available_keys"] == [[code, d] for d in dates]
        assert c["absent_keys"] == [] and c["ratio"] == 1
        assert c["expected_fact_units"] == c["available_fact_units"] == len(dates)
    dep = obs["sample_dependence_context"]
    assert dep["horizon"] == h and dep["ordered_anchors"] == anchors
    assert dep["spans"] == [{"anchor": a, "lookback": back[1]} for a, _, back, _ in endpoints]
    sample = job["projection"]["numeric_sample"]
    assert sample["values"] == values and sample["sample_count"] == len(values)
    assert sample["unit"] == "decimal_ratio"
    assert job["projection"]["binding"]["ordered_observation_keys"] == keys
    provenance = obs["provenance"]
    raw = base64.b64decode(provenance["canonical_input_bytes"]["value"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == provenance["input_fingerprint"]
    index_payload = [view["dataset"], view["view"], 1, [code], req["start_date"], req["end_date"],
                     [view["coverage"][k] for k in COVERAGE],
                     [[r[k] for k in ("index_code", "symbol", "name", "market", "publisher",
                                     "category", "trade_date")]
                      + [r[k].hex() for k in FLOATS] for r in view["records"]]]
    expected_keys = [[code, d] for d in sessions]
    assert json.loads(raw) == ["trailing_return_inputs_v2", "descriptive_missing_tolerant_v1",
                               identity, sorted(calendar_payload, key=lambda x: (x[4], x[5], x[3])),
                               index_payload, expected_keys, [], endpoints]
    assert provenance["expected_daily_keys"] == provenance["available_daily_keys"] == expected_keys
    assert provenance["absent_daily_keys"] == []
    assert provenance["endpoint_requirements"] == [
        {"anchor": a, "anchor_daily_key": front, "lookback_daily_key": back,
         "missing_required_facts": missing} for a, front, back, missing in endpoints]
    ordered = sorted(values)
    outcomes = job["analysis_outcomes"]
    assert len(outcomes) == len(requests) == 2
    for outcome, request in zip(outcomes, requests, strict=True):
        assert outcome["status"] == "success" and outcome["request"] == request
        assert outcome["association"]["request_id"] == request["request_id"]
        result, spec = outcome["statistical_result"], request["spec"]
        assert result["sample_count"] == len(values) and result["unit"] == "decimal_ratio"
        if spec["method"] == "quantile":
            assert result["estimator"] == "type7_linear_v1"
            quantiles = []
            for p in spec["points"]:
                at = (len(values) - 1) * p
                i, frac = int(at), at - int(at)
                v = ordered[i] if frac == 0 else ordered[i] + frac * (ordered[i + 1] - ordered[i])
                quantiles.append([p, v])
            assert result["points_and_values"] == quantiles
        else:
            assert result["edges"] == spec["edges"]
            assert len(result["bins"]) == len(spec["edges"]) - 1
            counts = []
            for i, bin in enumerate(result["bins"]):
                left, right = spec["edges"][i:i + 2]
                final = i == len(result["bins"]) - 1
                n = sum(left <= v and (v <= right if final else v < right) for v in values)
                assert (bin["left"], bin["right"], bin["left_inclusive"],
                        bin["right_inclusive"], bin["count"], bin["frequency"]) == (
                            left, right, True, final, n, n / len(values))
                counts.append(n)
            for tail, count in (("underflow", sum(v < spec["edges"][0] for v in values)),
                                ("overflow", sum(v > spec["edges"][-1] for v in values))):
                assert result[tail + "_count"] == count
                assert result[tail + "_frequency"] == count / len(values)
                counts.append(count)
            assert sum(counts) == len(values)
    return {"index": code, "name": meta[2], "horizon": h, "sample_count": len(values),
            "eligible": obs["eligible_count"], "unavailable": 0, "excluded": 0,
            "observation_coverage": 1.0, "market_fact_coverage": view["coverage"],
            "first_anchor": anchors[0], "last_anchor": anchors[-1], "warm_up_start": sessions[0],
            "metadata": dict(zip(("index_code", "symbol", "name", "market", "publisher",
                                   "category"), meta, strict=True)), "job_status": job["status"],
            "input_fingerprint": provenance["input_fingerprint"],
            "quantiles": outcomes[0]["statistical_result"],
            "interval_count": outcomes[1]["statistical_result"],
            "independent_export_oracles": "PASS", "observations_sha256": digest(values)}


def verify(run_id):
    def forbidden(*args, **kwargs):
        raise AssertionError("Saved-result verification must not access network or SQLite")

    with (patch.object(socket.socket, "connect", forbidden),
          patch.object(sqlite3, "connect", forbidden)):
        read = TOOL["G5"]["read_execution"](TOOL["STORE"], run_id)
        batch = read["batch_result"]
        assert read["status"] == "PASS" and batch["status"] == "success"
        assert (batch["planned_count"], batch["success_count"], batch["failed_count"],
                batch["skipped_count"]) == (16, 16, 0, 0)
        assert [(j["fixed_job_spec"]["subject"], j["fixed_job_spec"]["horizon"])
                for j in batch["job_results"]] == [(s, h) for s in TOOL["SUBJECTS"]
                                                   for h in (1, 3, 5, 10)]
        matrix = [verify_job(j, batch["plan"]["analysis_requests"]) for j in batch["job_results"]]
    return {"run_id": run_id, "result_artifact": read["result_artifact"], "jobs": matrix,
            "analyses_verified": 32, "independent_verification": "PASS",
            "network_and_sqlite_forbidden": True}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.run)
    TOOL["write"](args.output, result)
    print(json.dumps({"run": args.run, "jobs_verified": len(result["jobs"]),
                      "analyses_verified": result["analyses_verified"]}))
