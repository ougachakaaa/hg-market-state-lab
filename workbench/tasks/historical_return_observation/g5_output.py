"""Safe delivery projection of the existing public Research result, without computations."""

import base64
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date
from math import isfinite
from typing import Any

import data_lake
import data_lake.datasets.tushare_index_daily as index
import data_lake.datasets.tushare_trade_calendar as calendar
import market_research.descriptive.association as association
import market_research.descriptive.cases.trailing_return as case
import market_research.descriptive.conversion as conversion
import market_research.descriptive.execution as execution
import market_research.descriptive.observation as observation
import market_statistics

# Exact types exported by these public facades only, never arbitrary dataclasses/repr.
PUBLIC_VALUES = {
    value for module in (data_lake, index, calendar, association, case, conversion,
                         execution, observation, market_statistics)
    for value in vars(module).values() if isinstance(value, type) and is_dataclass(value)
}
OMITTED = {"omitted": "unsafe or unpublished value; no representation retained"}
TEXT_FIELDS = {"reason", "not_attempted_reason", "skip_reason"}


def public_value(value: Any) -> Any:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        return value if isfinite(value) else OMITTED.copy()
    if type(value) is date:
        return value.isoformat()
    if type(value) is bytes:
        return {"encoding": "base64", "value": base64.b64encode(value).decode("ascii")}
    if type(value) in (index.IndexDailyExport, calendar.TradeCalendarExport):
        row_type = index.IndexDailyRow if type(value) is index.IndexDailyExport else (
            calendar.TradeCalendarRecord)
        scope_fields = ("index_codes",) if type(value) is index.IndexDailyExport else ("exchange",)
        return {
            **{name: public_value(getattr(value, name)) for name in (
                "dataset", "view", "export_schema_version")},
            "scope": {k: public_value(getattr(value.scope, k, OMITTED)) for k in scope_fields},
            "window": {k: public_value(getattr(value.window, k, OMITTED))
                       for k in ("start_date", "end_date")},
            "coverage": (public_value(value.coverage) if type(value.coverage) is
                         data_lake.CoverageResult else OMITTED.copy()),
            "records": ([public_value(row) if type(row) is row_type else OMITTED.copy()
                         for row in value.records] if type(value.records) in (list, tuple)
                        else OMITTED.copy()),
        }
    if type(value) is case.InputAttempt:
        return {name: (public_value(item) if item is None or type(item) in allowed
                       else OMITTED.copy())
                for name, allowed in {
                    "request": (calendar.TradeCalendarRange, index.IndexDailyRange),
                    "preliminary_export": (calendar.TradeCalendarExport, index.IndexDailyExport),
                    "ensure_result": (data_lake.EnsureResult,),
                    "final_export": (calendar.TradeCalendarExport, index.IndexDailyExport),
                }.items() for item in (getattr(value, name),)}
    if type(value) in PUBLIC_VALUES:
        result = {f.name: public_value(getattr(value, f.name)) for f in fields(value)
                  if f.name != "error" and f.name not in TEXT_FIELDS}
        if any(f.name in TEXT_FIELDS or f.name == "error" for f in fields(value)):
            result["diagnostic_text_omitted"] = True
        return result
    if type(value) in (list, tuple):
        return [public_value(v) for v in value]
    # This admitted case only publishes empty metric parameters. Arbitrary malformed
    # diagnostic mappings can contain provider payloads or secrets; never traverse them.
    if isinstance(value, Mapping) and not value:
        return {}
    return OMITTED.copy()


def observation_json(source: Any) -> Any:
    if source is None:
        return None
    result = public_value(source)
    for name in ("candidate_count", "eligible_count", "unavailable_count", "excluded_count",
                 "observation_coverage", "unavailable_ratio", "excluded_ratio"):
        result[name] = getattr(source, name)
    for name in ("overall", "warm_up", "sample"):
        coverage = getattr(source.market_fact_coverage, name)
        result["market_fact_coverage"][name].update(
            expected_fact_units=coverage.expected_fact_units,
            available_fact_units=coverage.available_fact_units,
            absent_keys=public_value(coverage.absent_keys), ratio=coverage.ratio)
    return result


def batch_json(batch: execution.BatchResult, plan: execution.ResearchPlan) -> dict[str, Any]:
    if type(batch) is not execution.BatchResult or batch.plan != plan:
        raise ValueError("Expected actual public BatchResult of the exact frozen plan")
    execution.BatchResult(batch.plan, batch.job_results)  # Public carrier invariant validation.
    jobs = []
    for job in batch.job_results:
        outcomes = []
        for outcome in job.analysis_outcomes:
            outcomes.append({
                "request": public_value(outcome.request), "status": outcome.status,
                "statistical_result": public_value(outcome.statistical_result),
                "failure": public_value(outcome.failure),
                "association": ({"observation": "observation_set", "projection": "projection",
                                 "request_id": outcome.request_id,
                                 "statistical_result": "statistical_result"}
                                if outcome.associated_evidence is not None else None),
                "diagnostic_text_omitted": outcome.not_attempted_reason is not None,
            })
        projection = None if job.projection is None else {
            "numeric_sample": {**public_value(job.projection.numeric_sample),
                               "sample_count": job.projection.numeric_sample.sample_count},
            "binding": {"source_observation_reference": "observation_set",
                        "ordered_observation_keys": public_value(
                            job.projection.binding.ordered_observation_keys)},
        }
        jobs.append({"fixed_job_spec": public_value(job.fixed_job_spec),
                     "job_identity": public_value(job.job_identity), "status": job.status,
                     "analysis_outcomes": outcomes, "prepared_inputs": public_value(
                         job.prepared_inputs), "input_attempts": public_value(job.input_attempts),
                     "observation_set": observation_json(job.observation_set),
                     "projection": projection, "failures": public_value(job.failures),
                     "diagnostic_text_omitted": job.skip_reason is not None,
                     "triggering_failed_job_identity": public_value(
                         job.triggering_failed_job_identity)})
    return {"plan": public_value(batch.plan), "job_results": jobs, "status": batch.status,
            **{name: getattr(batch, name) for name in (
                "planned_count", "success_count", "failed_count", "skipped_count")}}


def validate_output(output: dict, preview: dict) -> str:
    """Verify delivery associations/accounting on read, never recalculate statistics."""
    def same(left: Any, right: Any) -> bool:
        return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
            right, sort_keys=True, allow_nan=False)

    if not same(output["plan"], preview["plan"]) or (
            len(output["job_results"]) != preview["planned_count"]):
        raise ValueError("Result/frozen plan linkage mismatch")
    counts = {"Success": 0, "Failed": 0, "Skipped": 0}
    for job, planned in zip(output["job_results"], preview["jobs"], strict=True):
        if any(not same(job[k], planned[k]) for k in ("fixed_job_spec", "job_identity")):
            raise ValueError("Result Job identity/order mismatch")
        counts[job["status"]] += 1
        outcomes = job["analysis_outcomes"]
        if not same([o["request"] for o in outcomes], preview["expected_analyses_per_job"]):
            raise ValueError("Result analysis identity/order mismatch")
        if job["status"] == "Success" and (job["failures"] or any(
                o["status"] != "success" or o["statistical_result"] is None
                or o["association"] != {"observation": "observation_set",
                    "projection": "projection", "request_id": o["request"]["request_id"],
                    "statistical_result": "statistical_result"} for o in outcomes)):
            raise ValueError("Successful Job lacks required successful analyses")
        if job["status"] == "Failed" and not job["failures"]:
            raise ValueError("Failed Job lacks failures")
    expected = {"planned_count": sum(counts.values()), "success_count": counts["Success"],
                "failed_count": counts["Failed"], "skipped_count": counts["Skipped"]}
    status = "success" if not counts["Failed"] else (
        "partial_success" if counts["Success"] else "failed")
    if any(type(output[k]) is not int or output[k] != v for k, v in expected.items()) or (
            output["status"] != status or not counts["Success"] + counts["Failed"]):
        raise ValueError("Result Batch accounting mismatch")
    return "PASS" if status == "success" and counts["Skipped"] == 0 else "FAIL"
