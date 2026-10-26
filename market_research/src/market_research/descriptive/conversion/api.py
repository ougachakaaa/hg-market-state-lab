"""Pure outbound adaptation; no market formula or statistics execution."""

from market_statistics import InvalidSample, NumericSample

from ..observation import ObservationSet
from .failures import NoEligibleObservations, UnmappableSample
from .models import SampleBinding, SampleProjection
from .validation import validate_source


def convert[Provenance](
    observation_set: ObservationSet[Provenance],
) -> SampleProjection[Provenance]:
    validate_source(observation_set)
    if not observation_set.eligible_count:
        raise NoEligibleObservations("The valid ObservationSet contains no Eligible observations")
    eligible = observation_set.eligible_observations
    try:
        sample = NumericSample(
            tuple(item.scalar_value for item in eligible),
            observation_set.observation_definition.unit,
        )
    except InvalidSample as exc:
        raise UnmappableSample(str(exc)) from exc
    binding = SampleBinding(observation_set, tuple(item.observation_key for item in eligible))
    return SampleProjection(sample, binding)
