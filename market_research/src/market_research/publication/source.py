"""Explicit V1 serialization and retention of admitted public Research evidence."""

import base64
import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any

import data_lake as dl
import data_lake.datasets.tushare_index_daily as idx
import data_lake.datasets.tushare_trade_calendar as cal
import market_statistics as st
from market_research.descriptive import association as assoc
from market_research.descriptive import conversion as conv
from market_research.descriptive import execution as ex
from market_research.descriptive import observation as obs
from market_research.descriptive.cases import trailing_return as case

from .errors import InvalidPublicationInput, PublicationCollision, PublicationUnavailable

# Explicit fields for the admitted public vocabulary; adding a type requires a V1
# contract decision, never automatic serialization of arbitrary dataclasses.
_FIELDS: dict[type, str] = {
    ex.BatchResult: "plan job_results",
    ex.ResearchPlan: (
        "metric metric_parameters subjects horizons windows analysis_requests on_job_failure"
    ),
    ex.JobResult: (
        "fixed_job_spec job_identity status analysis_outcomes "
        "prepared_inputs observation_set projection failures skip_reason "
        "triggering_failed_job_identity"
    ),
    ex.AnalysisOutcome: (
        "request status statistical_result associated_evidence failure not_attempted_reason"
    ),
    ex.FailureRecord: "job_identity failure_stage failure_category reason error request_id",
    assoc.AnalysisRequest: "request_id spec",
    assoc.ResearchAnalysisEvidence: "request statistical_result projection",
    conv.SampleProjection: "numeric_sample binding",
    conv.SampleBinding: "source_observation_reference ordered_observation_keys",
    obs.DateWindow: "start_date end_date",
    obs.ObservationJobSpec: "subject metric metric_parameters horizon historical_sample_window",
    obs.ObservationDefinition: (
        "metric grain key_definition formula unit horizon_unit calendar anchor_meaning bounds"
    ),
    obs.RequiredFact: "dataset view export_schema_version subject trade_date field",
    obs.MissingDependency: "endpoint_role fact reason input_reference diagnostic_reasons",
    obs.EndpointFact: "endpoint_role fact value",
    obs.EligibleObservation: "observation_key anchor scalar_value",
    obs.UnavailableObservation: "observation_key anchor missing_dependencies available_endpoints",
    obs.ExcludedObservation: "observation_key anchor reason_code reason offending_facts",
    obs.FactCoverage: "expected_keys available_keys",
    obs.MarketFactCoverage: "overall warm_up sample",
    obs.ObservationSpan: "anchor lookback",
    obs.SampleDependenceContext: "horizon horizon_unit ordered_anchors spans interpretation",
    obs.ObservationSet: (
        "job_identity fixed_job_spec observation_definition "
        "candidate_anchors eligible_observations unavailable_observations "
        "excluded_observations market_fact_coverage provenance "
        "sample_dependence_context"
    ),
    case.EndpointRequirement: "anchor anchor_daily_key lookback_daily_key missing_required_facts",
    case.TrailingReturnProvenance: (
        "prepared_inputs endpoint_requirements expected_daily_keys "
        "available_daily_keys absent_daily_keys canonical_input_bytes "
        "input_fingerprint input_profile"
    ),
    case.InputAttempt: "request preliminary_export ensure_result final_export",
    case.CalendarInput: "request final_export",
    case.IndexInput: "request final_export",
    case.PreparedInputs: "job_identity calendar_slices index_slice attempts",
    dl.CoverageResult: (
        "requested_units successful_units missing_units pending_units failed_units complete"
    ),
    dl.EnsureResult: (
        "requested_units already_successful_units attempted_units "
        "succeeded_units failed_units records_written complete failures"
    ),
    dl.UnitFailure: "identity reason",
    idx.IndexDailyRange: "index_codes start_date end_date",
    idx.IndexDailyScope: "index_codes",
    idx.IndexDailyRow: (
        "index_code symbol name market publisher category trade_date open "
        "high low close pre_close change pct_change volume amount"
    ),
    cal.TradeCalendarRange: "exchange start_date end_date",
    cal.TradeCalendarRecord: "exchange cal_date is_open pretrade_date",
    st.NumericSample: "values unit",
    st.QuantileSpec: "method points",
    st.IntervalCountSpec: "method edges unit",
    st.QuantileResult: "method estimator points_and_values sample_count unit",
    st.IntervalBin: "left right left_inclusive right_inclusive count frequency",
    st.IntervalCountResult: (
        "method edges bins underflow_count overflow_count "
        "underflow_frequency overflow_frequency sample_count unit"
    ),
}
_EXCEPTIONS: dict[type, tuple[str, ...]] = {
    ValueError: (),
    TypeError: (),
    RuntimeError: (),
    ArithmeticError: (),
    obs.ObservationConstructionFailure: (),
    conv.InvalidObservationSet: (),
    conv.NoEligibleObservations: (),
    conv.UnmappableSample: (),
    st.InvalidSample: (),
    st.InvalidStatisticalSpec: (),
    st.CalculationFailure: ("method", "reason"),
    assoc.ResultAssociationFailure: ("reason", "request_id", "job_identity"),
    case.InputPreparationFailure: ("request", "evidence"),
    case.InvalidPublicInput: ("request", "evidence"),
    case.IncompleteInput: ("request", "evidence"),
    case.HistoryInsufficient: ("request", "evidence"),
    case.UpstreamFailure: ("request", "evidence"),
    dl.InvalidRequestError: (),
    dl.OperationError: (),
}


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
    except (ValueError, TypeError, OverflowError) as exc:
        raise InvalidPublicationInput(f"invalid JSON value: {exc}") from exc


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: object, active: set[int] | None = None) -> Any:
    """Encode only explicitly admitted types; never invoke arbitrary serialization."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InvalidPublicationInput("non-finite source value")
        return value
    if type(value) is date:
        return {"$date": value.isoformat()}
    if type(value) is bytes:
        return {"$bytes_base64": base64.b64encode(value).decode("ascii")}
    if active is None:
        active = set()
    if id(value) in active:
        raise InvalidPublicationInput("cyclic source evidence")
    active.add(id(value))
    item: Any = value
    try:
        if type(value) in (tuple, list):
            return {
                "$tuple" if type(value) is tuple else "$list": [encode(v, active) for v in item]
            }
        if type(value) in (dict, MappingProxyType):
            mapping = item
            if not all(type(k) is str for k in mapping):
                raise InvalidPublicationInput("source mapping keys must be strings")
            return {"$mapping": {k: encode(v, active) for k, v in mapping.items()}}
        if type(value) in (cal.TradeCalendarExport, idx.IndexDailyExport):
            # The upstream public envelope defines these two structural views; their
            # scope/window implementation classes are not public import surfaces.
            scope = item.scope
            window = item.window
            scope_field = "exchange" if type(value) is cal.TradeCalendarExport else "index_codes"
            fields = {
                "dataset": item.dataset,
                "view": item.view,
                "export_schema_version": item.export_schema_version,
                "scope": {scope_field: getattr(scope, scope_field)},
                "window": {"start_date": window.start_date, "end_date": window.end_date},
                "coverage": item.coverage,
                "records": item.records,
            }
            return {
                "$type": type(value).__name__,
                "fields": {k: encode(v, active) for k, v in fields.items()},
            }
        if type(value) in _FIELDS:
            return {
                "$type": type(value).__name__,
                "fields": {
                    field: encode(getattr(value, field), active)
                    for field in _FIELDS[type(value)].split()
                },
            }
        if type(value) in _EXCEPTIONS:
            error = value
            assert isinstance(error, Exception)
            return {
                "$error": type(error).__name__,
                "args": encode(error.args, active),
                "fields": {f: encode(getattr(error, f), active) for f in _EXCEPTIONS[type(error)]},
                "cause": encode(error.__cause__, active),
            }
        raise InvalidPublicationInput(
            f"unsupported source type: {type(value).__module__}.{type(value).__qualname__}"
        )
    finally:
        active.remove(id(value))


def validate_batch(batch: ex.BatchResult) -> None:
    if type(batch) is not ex.BatchResult:
        raise InvalidPublicationInput("expected completed public BatchResult")
    try:
        batch.__post_init__()
        for job in batch.job_results:
            if job.observation_set is not None:
                provenance = job.observation_set.provenance
                if (
                    type(provenance) is not case.TrailingReturnProvenance
                    or digest(provenance.canonical_input_bytes) != provenance.input_fingerprint
                ):
                    raise InvalidPublicationInput("source input provenance fingerprint mismatch")
                case.verify_input_provenance(job.fixed_job_spec, provenance)
                if provenance.prepared_inputs is not job.prepared_inputs:
                    raise InvalidPublicationInput("provenance prepared inputs mismatch")
            for outcome in job.analysis_outcomes:
                if outcome.status == "success":
                    assert job.observation_set is not None and job.projection is not None
                    assert outcome.statistical_result is not None
                    assoc.associate(
                        job.fixed_job_spec,
                        job.observation_set,
                        job.projection,
                        outcome.request,
                        outcome.statistical_result,
                    )
    except InvalidPublicationInput:
        raise
    except (
        ValueError,
        TypeError,
        AttributeError,
        AssertionError,
        case.InputPreparationFailure,
    ) as exc:
        raise InvalidPublicationInput(f"invalid batch evidence: {exc}") from exc


def source_bytes(batch: ex.BatchResult, source_id: str) -> bytes:
    if type(source_id) is not str or not source_id:
        raise InvalidPublicationInput("source_id must be a nonempty string")
    validate_batch(batch)
    return canonical_json(
        {"schema": "research-source-v1", "source_id": source_id, "batch": encode(batch)}
    )


@dataclass(frozen=True)
class SourceReference:
    source_id: str
    location: str
    sha256: str
    size: int


def retain_source(batch: ex.BatchResult, source_id: str, path: str | Path) -> SourceReference:
    """Exclusively retain a completed Batch; caller controls the source location."""
    data = source_bytes(batch, source_id)
    location = os.path.abspath(os.fspath(path))
    try:
        fd = os.open(location, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise PublicationCollision("source location already exists") from exc
    except OSError as exc:
        raise PublicationUnavailable("cannot retain source evidence") from exc
    return SourceReference(source_id, location, digest(data), len(data))
