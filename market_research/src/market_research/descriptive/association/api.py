"""A successful association retains all original inputs and performs no orchestration."""

from market_statistics import InvalidSample, InvalidStatisticalSpec, StatisticalResult

from ..conversion import SampleProjection
from ..observation import (
    JobIdentity,
    ObservationConstructionFailure,
    ObservationJobSpec,
    ObservationSet,
)
from .failures import ResultAssociationFailure
from .models import AnalysisRequest, ResearchAnalysisEvidence
from .results import validate_result
from .source import fixed_identity, require, validate_projection


def associate[P](
    fixed_job: ObservationJobSpec,
    observation_set: ObservationSet[P],
    projection: SampleProjection[P],
    request: AnalysisRequest,
    statistical_result: StatisticalResult,
) -> ResearchAnalysisEvidence[P]:
    request_id = None
    if isinstance(request, AnalysisRequest):
        candidate = getattr(request, "request_id", None)
        if isinstance(candidate, str) and candidate:
            request_id = candidate
    identity: JobIdentity | None = None
    try:
        identity = fixed_identity(fixed_job, observation_set)
        validate_projection(observation_set, projection, identity)
        require(type(request) is AnalysisRequest, "Expected public AnalysisRequest")
        AnalysisRequest.__post_init__(request)
        validate_result(projection.numeric_sample, request.spec, statistical_result)
    except ResultAssociationFailure as exc:
        # Keep the original failure and cause; enrich only safely identified context.
        if exc.request_id is None:
            exc.request_id = request_id
        if exc.job_identity is None:
            exc.job_identity = identity
        raise
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        ObservationConstructionFailure,
        InvalidSample,
        InvalidStatisticalSpec,
    ) as exc:
        raise ResultAssociationFailure(
            str(exc),
            request_id=request_id,
            job_identity=identity,
        ) from exc
    return ResearchAnalysisEvidence(request, statistical_result, projection)
