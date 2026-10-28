"""Project existing public results without calculations, truncation or private access."""

from collections.abc import Sized
from typing import cast

from pydantic import ValidationError

from market_research.descriptive.execution import BatchResult, FailureRecord, JobResult, PlanPreview

from .requests import AnalysisBody, plan_body, spec_body
from .schemas import (
    AnalysisOutcomeBody,
    BatchResponse,
    CalendarRequestBody,
    EnsureSummary,
    ExportSummary,
    FailureBody,
    FixedJobBody,
    IndexRequestBody,
    InputAttemptBody,
    InputRequestBody,
    InvalidPublicShape,
    JobIdentityBody,
    JobResultBody,
    NumericSampleBody,
    ObservationKeyBody,
    ObservationSetBody,
    PlannedJobBody,
    PreparedContextBody,
    PreparedSliceBody,
    PreviewResponse,
    ProjectionBody,
)

SOURCE_LIMITATION = (
    "Source fingerprint identifies consumed inputs, not authenticated numerical origin. "
    "Lookback spans may overlap/share facts; no independence, causality or predictive validity. "
    "Full input exports, canonical bytes and original exceptions/diagnostics remain Python-only."
)
SKIP_REASON = "Not attempted: on_job_failure=stop after the first Failed Job"


def preview_response(preview: PlanPreview) -> PreviewResponse:
    return PreviewResponse(
        plan=plan_body(preview.plan),
        jobs=tuple(PlannedJobBody.model_validate(j) for j in preview.jobs),
        planned_count=preview.planned_count,
        analysis_attempt_count=preview.analysis_attempt_count,
    )


def failure_body(failure: FailureRecord) -> FailureBody:
    return FailureBody(
        job_identity=JobIdentityBody.model_validate(failure.job_identity),
        failure_stage=failure.failure_stage,
        failure_category=failure.failure_category,
        reason=f"{failure.failure_category} during {failure.failure_stage}; "
        "original diagnostic is available in Python.",
        request_id=failure.request_id,
    )


def request_body(request: object) -> InputRequestBody:
    if hasattr(request, "exchange"):
        return CalendarRequestBody.model_validate(request)
    return IndexRequestBody.model_validate(request)


def export_summary(value: object) -> ExportSummary | InvalidPublicShape | None:
    if value is None:
        return None
    try:
        fields = ("dataset", "view", "export_schema_version", "coverage", "records")
        attributes = {name: getattr(value, name) for name in fields}
        records = cast(Sized, attributes.pop("records"))
        return ExportSummary.model_validate({**attributes, "record_count": len(records)})
    except (AttributeError, TypeError, ValueError):
        return InvalidPublicShape()


def ensure_summary(value: object) -> EnsureSummary | InvalidPublicShape | None:
    if value is None:
        return None
    try:
        return EnsureSummary.model_validate(value)
    except (AttributeError, TypeError, ValidationError):
        return InvalidPublicShape()


def prepared_slice(request: object, export: object) -> PreparedSliceBody:
    summary = export_summary(export)
    if not isinstance(summary, ExportSummary):
        raise ValueError("PreparedInputs must retain valid public exports")
    return PreparedSliceBody(request=request_body(request), final_export=summary)


def job_response(job: JobResult) -> JobResultBody:
    observations = job.observation_set
    projection = job.projection
    prepared = job.prepared_inputs
    blocking_reason = (
        SKIP_REASON
        if job.status == "Skipped"
        else failure_body(job.failures[0]).reason
        if job.failures
        else None
    )
    return JobResultBody(
        fixed_job_spec=FixedJobBody.model_validate(job.fixed_job_spec),
        job_identity=JobIdentityBody.model_validate(job.job_identity),
        status=job.status,
        skip_reason=SKIP_REASON if job.skip_reason is not None else None,
        triggering_failed_job_identity=(
            JobIdentityBody.model_validate(job.triggering_failed_job_identity)
            if job.triggering_failed_job_identity is not None
            else None
        ),
        analysis_outcomes=tuple(
            AnalysisOutcomeBody.model_validate(
                {
                    "request": AnalysisBody(request_id=o.request_id, spec=spec_body(o.spec)),
                    "status": o.status,
                    "statistical_result": o.statistical_result,
                    "associated": o.associated_evidence is not None,
                    "failure": failure_body(o.failure) if o.failure is not None else None,
                    "not_attempted_reason": blocking_reason
                    if o.status == "not_attempted"
                    else None,
                }
            )
            for o in job.analysis_outcomes
        ),
        failures=tuple(failure_body(f) for f in job.failures),
        input_attempts=tuple(
            InputAttemptBody(
                request=request_body(a.request),
                preliminary_export=export_summary(a.preliminary_export),
                ensure_result=ensure_summary(a.ensure_result),
                final_export=export_summary(a.final_export),
            )
            for a in job.input_attempts
        ),
        prepared_context=PreparedContextBody(
            calendar_slices=tuple(
                prepared_slice(s.request, s.final_export) for s in prepared.calendar_slices
            ),
            index_slice=(
                prepared_slice(prepared.index_slice.request, prepared.index_slice.final_export)
                if prepared.index_slice is not None
                else None
            ),
        )
        if prepared is not None
        else None,
        observation_set=ObservationSetBody.model_validate(observations)
        if observations is not None
        else None,
        projection=ProjectionBody(
            numeric_sample=NumericSampleBody.model_validate(projection.numeric_sample),
            ordered_observation_keys=tuple(
                ObservationKeyBody.model_validate(k)
                for k in projection.binding.ordered_observation_keys
            ),
            source_job_identity=JobIdentityBody.model_validate(
                projection.binding.source_observation_reference.job_identity
            ),
            source_input_fingerprint=projection.binding.business_provenance.input_fingerprint,
        )
        if projection is not None
        else None,
    )


def batch_response(batch: BatchResult) -> BatchResponse:
    return BatchResponse(
        plan=plan_body(batch.plan),
        status=batch.status,
        planned_count=batch.planned_count,
        success_count=batch.success_count,
        failed_count=batch.failed_count,
        skipped_count=batch.skipped_count,
        job_results=tuple(job_response(j) for j in batch.job_results),
        source_identity_limitation=SOURCE_LIMITATION,
    )
