"""Pure Publication JSON, identity, evidence and result-association validation."""

import json
import math
import os
import re
import uuid
from typing import Any

from market_statistics import IntervalBin, IntervalCountResult, QuantileResult

from .errors import (
    InconsistentPublication,
    InvalidPublicationInput,
    PublicationCorrupt,
    UnsupportedPublicationVersion,
)
from .source import canonical_json, digest

_ID = re.compile(r"[0-9a-f]{64}\Z")
_UUID = re.compile(r"[0-9a-f]{32}\Z")


def _uuid(value: object) -> str:
    if type(value) is not str or not _UUID.fullmatch(value):
        raise InvalidPublicationInput("invalid publication identity")
    try:
        if uuid.UUID(hex=value).version != 4:
            raise ValueError
    except ValueError as exc:
        raise InvalidPublicationInput("publication identity must be a UUID4 hex") from exc
    return value


def _id(value: object) -> str:
    if type(value) is not str or not _ID.fullmatch(value):
        raise InvalidPublicationInput("invalid publication-local reference")
    return value


def _json(data: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def finite_float(text: str) -> float:
        value = float(text)
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return value

    try:
        return json.loads(
            data,
            parse_float=finite_float,
            object_pairs_hook=pairs,
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise PublicationCorrupt("invalid JSON") from exc


def _shape(obj: Any, keys: set[str], description: str) -> dict[str, Any]:
    if type(obj) is not dict or set(obj) != keys:
        raise PublicationCorrupt(f"invalid {description} structure")
    return obj


def _schema(obj: dict[str, Any], expected: str) -> None:
    if obj.get("schema") != expected:
        raise UnsupportedPublicationVersion(f"unsupported {expected} schema")


def _entry(data: bytes) -> dict[str, Any]:
    return {"sha256": digest(data), "size": len(data)}


def _integrity_entry(metadata: object) -> dict[str, Any]:
    info = _shape(metadata, {"sha256", "size"}, "integrity entry")
    if (
        type(info["sha256"]) is not str
        or not _ID.fullmatch(info["sha256"])
        or type(info["size"]) is not int
        or info["size"] < 0
    ):
        raise PublicationCorrupt("invalid integrity entry")
    return info


def _verified(data: bytes, metadata: object) -> None:
    info = _integrity_entry(metadata)
    if len(data) != info["size"] or digest(data) != info["sha256"]:
        raise PublicationCorrupt("content integrity mismatch")


def _carrier(value: object, type_name: str) -> dict[str, Any]:
    obj = _shape(value, {"$type", "fields"}, f"{type_name} source carrier")
    if obj["$type"] != type_name or type(obj["fields"]) is not dict:
        raise InconsistentPublication(f"wrong {type_name} source carrier")
    return obj["fields"]


def _tuple(value: object) -> list[Any]:
    obj = _shape(value, {"$tuple"}, "source tuple")
    if type(obj["$tuple"]) is not list:
        raise PublicationCorrupt("invalid source tuple")
    return obj["$tuple"]


def _coverage_summary(job: dict[str, Any]) -> dict[str, Any] | None:
    if "observation_set" not in job:
        raise PublicationCorrupt("missing observation context")
    if job["observation_set"] is None:
        return None
    try:
        obs = _carrier(job["observation_set"], "ObservationSet")
        if obs["job_identity"] != job["job_identity"]:
            raise InconsistentPublication("observation identity mismatch")
        counts = [
            len(_tuple(obs[k]))
            for k in (
                "candidate_anchors",
                "eligible_observations",
                "unavailable_observations",
                "excluded_observations",
            )
        ]
        candidate, eligible, unavailable, excluded = counts
        if candidate != eligible + unavailable + excluded:
            raise InconsistentPublication("observation population mismatch")
        market = _carrier(obs["market_fact_coverage"], "MarketFactCoverage")
        facts = {}
        for name in ("overall", "warm_up", "sample"):
            part = _carrier(market[name], "FactCoverage")
            expected, available = (
                len(_tuple(part[k])) for k in ("expected_keys", "available_keys")
            )
            if available > expected:
                raise InconsistentPublication("fact coverage mismatch")
            facts[name] = {
                "expected_fact_count": expected,
                "available_fact_count": available,
                "coverage_ratio": available / expected if expected else None,
            }
        definition = _carrier(obs["observation_definition"], "ObservationDefinition")
        provenance = _carrier(obs["provenance"], "TrailingReturnProvenance")
        unit, profile, fingerprint = (
            definition["unit"],
            provenance["input_profile"],
            provenance["input_fingerprint"],
        )
        if (
            unit != "decimal_ratio"
            or profile != "trailing_return_inputs_v2"
            or not isinstance(fingerprint, str)
            or not _ID.fullmatch(fingerprint)
        ):
            raise InconsistentPublication("invalid coverage provenance")
        return {
            "candidate_count": candidate,
            "eligible_count": eligible,
            "unavailable_count": unavailable,
            "excluded_count": excluded,
            "observation_coverage": eligible / candidate if candidate else None,
            "unavailable_ratio": unavailable / candidate if candidate else None,
            "excluded_ratio": excluded / candidate if candidate else None,
            "market_facts": facts,
            "observation_unit": unit,
            "input_profile": profile,
            "input_fingerprint": fingerprint,
        }
    except (KeyError, TypeError, IndexError) as exc:
        raise PublicationCorrupt("malformed observation coverage") from exc


def _verify_source_associations(
    source: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    batch = _carrier(source["batch"], "BatchResult")
    if batch.get("plan") != manifest["scope"]:
        raise InconsistentPublication("manifest scope differs from retained source")
    jobs = _tuple(batch.get("job_results"))
    if len(jobs) != len(manifest["jobs"]):
        raise InconsistentPublication("source job count mismatch")
    records: dict[str, dict[str, Any]] = {}
    statuses = []
    for encoded_job, summary_job in zip(jobs, manifest["jobs"], strict=True):
        job = _carrier(encoded_job, "JobResult")
        for field in (
            "job_identity",
            "status",
            "skip_reason",
            "triggering_failed_job_identity",
        ):
            if job.get(field) != summary_job[field]:
                raise InconsistentPublication("source job association mismatch")
        if job.get("projection") is not None:
            projection = _carrier(job["projection"], "SampleProjection")
            binding = _carrier(projection.get("binding"), "SampleBinding")
            if job.get("observation_set") is None or (
                binding.get("source_observation_reference") != job["observation_set"]
            ):
                raise InconsistentPublication("projection observation association mismatch")
        elif job["status"] == "Success":
            raise InconsistentPublication("successful job missing projection")
        failure_summaries = []
        for encoded_failure in _tuple(job.get("failures")):
            failure = _carrier(encoded_failure, "FailureRecord")
            failure_summaries.append(
                {
                    key: failure.get(key)
                    for key in ("failure_stage", "failure_category", "reason", "request_id")
                }
            )
        if failure_summaries != summary_job["failures"]:
            raise InconsistentPublication("source job failure association mismatch")
        statuses.append(job["status"])
        outcomes = _tuple(job.get("analysis_outcomes"))
        if len(outcomes) != len(summary_job["analyses"]):
            raise InconsistentPublication("source outcome count mismatch")
        for encoded_outcome, aid in zip(outcomes, summary_job["analyses"], strict=True):
            outcome = _carrier(encoded_outcome, "AnalysisOutcome")
            request = _carrier(outcome.get("request"), "AnalysisRequest")
            summary = next(a for a in manifest["analyses"] if a["analysis_id"] == aid)
            if (
                request.get("request_id") != summary["request_id"]
                or request.get("spec") != summary["spec"]
                or outcome.get("status") != summary["status"]
            ):
                raise InconsistentPublication("source request or outcome association mismatch")
            if outcome["status"] == "success":
                evidence = _carrier(outcome.get("associated_evidence"), "ResearchAnalysisEvidence")
                if (
                    evidence.get("request") != outcome["request"]
                    or evidence.get("statistical_result") != outcome["statistical_result"]
                    or evidence.get("projection") != job.get("projection")
                ):
                    raise InconsistentPublication("source successful evidence mismatch")
            records[aid] = {"outcome": outcome, "job": job}
    actual_status = (
        "success"
        if "Failed" not in statuses
        else ("partial_success" if "Success" in statuses else "failed")
    )
    if actual_status != manifest["status"]:
        raise InconsistentPublication("source batch status mismatch")
    return records


def _decode_result(value: object) -> QuantileResult | IntervalCountResult:
    """Read only the two explicit result variants; never dynamically import types."""
    try:
        obj = _shape(value, {"$type", "fields"}, "statistical result")
        if obj["$type"] == "QuantileResult":
            fields = _shape(
                obj["fields"],
                {"method", "estimator", "points_and_values", "sample_count", "unit"},
                "quantile result",
            )
            pairs = tuple(tuple(_tuple(pair)) for pair in _tuple(fields["points_and_values"]))
            if (
                fields["method"] != "quantile"
                or fields["estimator"] != "type7_linear_v1"
                or any(len(pair) != 2 for pair in pairs)
            ):
                raise PublicationCorrupt("invalid retained quantile result")
            return QuantileResult(pairs, fields["sample_count"], fields["unit"])
        if obj["$type"] == "IntervalCountResult":
            fields = _shape(
                obj["fields"],
                {
                    "method",
                    "edges",
                    "bins",
                    "underflow_count",
                    "overflow_count",
                    "underflow_frequency",
                    "overflow_frequency",
                    "sample_count",
                    "unit",
                },
                "interval result",
            )
            if fields["method"] != "interval_count":
                raise PublicationCorrupt("invalid retained interval result")
            bins = []
            for encoded in _tuple(fields["bins"]):
                data = _carrier(encoded, "IntervalBin")
                _shape(
                    data,
                    {"left", "right", "left_inclusive", "right_inclusive", "count", "frequency"},
                    "interval bin",
                )
                bins.append(IntervalBin(**data))
            return IntervalCountResult(
                tuple(_tuple(fields["edges"])),
                tuple(bins),
                fields["underflow_count"],
                fields["overflow_count"],
                fields["underflow_frequency"],
                fields["overflow_frequency"],
                fields["sample_count"],
                fields["unit"],
            )
        raise UnsupportedPublicationVersion("unsupported statistical result")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise PublicationCorrupt("malformed retained statistical result") from exc


def _analysis_id(source_id: str, job_identity: Any, request_id: str, spec: Any) -> str:
    return digest(canonical_json(["analysis-v1", source_id, job_identity, request_id, spec]))


def _validate_manifest(manifest: object, publication_id: str, payloads: dict[str, Any]) -> None:
    m = _shape(
        manifest,
        {"schema", "publication_id", "context", "scope", "status", "source", "jobs", "analyses"},
        "manifest",
    )
    _schema(m, "publication-manifest-v1")
    if m["publication_id"] != publication_id or type(m["context"]) is not str or not m["context"]:
        raise InconsistentPublication("publication identity/context mismatch")
    if (
        m["status"] not in ("success", "partial_success", "failed")
        or type(m["jobs"]) is not list
        or type(m["analyses"]) is not list
    ):
        raise PublicationCorrupt("invalid manifest status or lists")
    source = _shape(m["source"], {"source_id", "location", "sha256", "size"}, "source reference")
    if (
        type(source["source_id"]) is not str
        or not source["source_id"]
        or type(source["location"]) is not str
        or not os.path.isabs(source["location"])
    ):
        raise PublicationCorrupt("invalid source reference")
    if (
        type(source["sha256"]) is not str
        or not _ID.fullmatch(source["sha256"])
        or type(source["size"]) is not int
        or source["size"] < 0
        or payloads["source"] != {"sha256": source["sha256"], "size": source["size"]}
    ):
        raise InconsistentPublication("invalid source integrity reference")
    for group in ("analyses", "views", "layers"):
        if type(payloads[group]) is not dict or any(
            not isinstance(key, str) or not _ID.fullmatch(key) for key in payloads[group]
        ):
            raise PublicationCorrupt("invalid payload index")
        for metadata in payloads[group].values():
            _integrity_entry(metadata)
    seen_analyses: set[str] = set()
    seen_views: set[str] = set()
    seen_layers: set[str] = set()
    for summary in m["analyses"]:
        _shape(
            summary,
            {"analysis_id", "job_identity", "request_id", "spec", "status", "source_id", "views"},
            "analysis summary",
        )
        aid = summary["analysis_id"]
        if not isinstance(aid, str) or not _ID.fullmatch(aid) or aid in seen_analyses:
            raise PublicationCorrupt("invalid or duplicate analysis identity")
        if (
            type(summary["request_id"]) is not str
            or not summary["request_id"]
            or summary["source_id"] != source["source_id"]
        ):
            raise InconsistentPublication("invalid analysis source/request")
        if aid != _analysis_id(
            source["source_id"], summary["job_identity"], summary["request_id"], summary["spec"]
        ):
            raise InconsistentPublication("analysis identity mismatch")
        if (
            summary["status"] not in ("success", "failed", "not_attempted")
            or type(summary["views"]) is not list
        ):
            raise PublicationCorrupt("invalid analysis status/views")
        seen_analyses.add(aid)
        for view in summary["views"]:
            _shape(view, {"view_id", "layer_id", "measure"}, "view reference")
            vid, lid, measure = view["view_id"], view["layer_id"], view["measure"]
            if (
                measure not in ("quantile", "count", "frequency")
                or vid != digest(canonical_json(["view-v1", publication_id, aid, measure]))
                or lid != digest(canonical_json(["layer-v1", publication_id, aid, measure]))
                or vid in seen_views
                or lid in seen_layers
            ):
                raise InconsistentPublication("invalid or duplicate view identity")
            seen_views.add(vid)
            seen_layers.add(lid)
        if summary["status"] != "success" and summary["views"]:
            raise InconsistentPublication("unsuccessful analysis has a view")
        spec = _shape(summary["spec"], {"$type", "fields"}, "statistical spec")
        if spec["$type"] not in ("QuantileSpec", "IntervalCountSpec"):
            raise UnsupportedPublicationVersion("unsupported statistical spec")
        expected_measures = (
            ["quantile"] if spec["$type"] == "QuantileSpec" else ["count", "frequency"]
        )
        if (
            summary["status"] == "success"
            and [v["measure"] for v in summary["views"]] != expected_measures
        ):
            raise InconsistentPublication("successful analysis projections are incomplete")
    if (
        seen_analyses != set(payloads["analyses"])
        or seen_views != set(payloads["views"])
        or seen_layers != set(payloads["layers"])
    ):
        raise InconsistentPublication("manifest and payload index disagree")
    linked: list[str] = []
    for job in m["jobs"]:
        _shape(
            job,
            {
                "job_identity",
                "status",
                "failures",
                "skip_reason",
                "triggering_failed_job_identity",
                "analyses",
            },
            "job summary",
        )
        if (
            job["status"] not in ("Success", "Failed", "Skipped")
            or type(job["analyses"]) is not list
        ):
            raise PublicationCorrupt("invalid job summary")
        for aid in job["analyses"]:
            matches = [
                a
                for a in m["analyses"]
                if a["analysis_id"] == aid and a["job_identity"] == job["job_identity"]
            ]
            if len(matches) != 1:
                raise InconsistentPublication("job/analysis association mismatch")
            linked.append(aid)
    if len(linked) != len(seen_analyses) or set(linked) != seen_analyses:
        raise InconsistentPublication("incomplete job/analysis associations")
