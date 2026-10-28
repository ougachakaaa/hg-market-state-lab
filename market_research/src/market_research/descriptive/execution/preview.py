"""Immutable pure view of the existing whole-plan preflight and expansion."""

from dataclasses import dataclass

from ..observation import JobIdentity, ObservationJobSpec
from .plan import ResearchPlan, preflight_plan


@dataclass(frozen=True)
class PlannedJob:
    fixed_job_spec: ObservationJobSpec
    job_identity: JobIdentity


@dataclass(frozen=True)
class PlanPreview:
    plan: ResearchPlan
    jobs: tuple[PlannedJob, ...]

    @property
    def planned_count(self) -> int:
        return len(self.jobs)

    @property
    def analysis_attempt_count(self) -> int:
        return self.planned_count * len(self.plan.analysis_requests)


def preview_plan(plan: ResearchPlan) -> PlanPreview:
    return PlanPreview(
        plan, tuple(PlannedJob(job, identity) for job, identity in preflight_plan(plan))
    )
