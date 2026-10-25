"""Independent Observation entry, with no research execution dependency."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ObservationJobSpec, ObservationSet

if TYPE_CHECKING:
    from ..cases.trailing_return.identity import TrailingReturnProvenance


def observe(job_spec: ObservationJobSpec) -> ObservationSet[TrailingReturnProvenance]:
    from ..cases.trailing_return import construct_observations, prepare_inputs

    return construct_observations(job_spec, prepare_inputs(job_spec))
