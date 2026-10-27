"""Pure public preflight, reusing the case's existing validation and identity."""

from ...observation import JobIdentity, ObservationJobSpec
from .inputs import job_identity
from .inputs import validate_job as _validate_job


def validate_job(job: ObservationJobSpec) -> JobIdentity:
    _validate_job(job)
    return job_identity(job)
