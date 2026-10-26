"""Association failures never reclassify Statistics computation failures."""

from ..observation import JobIdentity


class ResultAssociationFailure(ValueError):
    """No evidence was produced; the caller still holds every original input."""

    stage = "result_association"
    category = "ResultAssociationFailure"

    def __init__(
        self,
        reason: str,
        *,
        request_id: str | None = None,
        job_identity: JobIdentity | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.request_id = request_id
        self.job_identity = job_identity
