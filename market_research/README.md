# Research Observation usage

This is usage documentation. Contracts are owned by [the module authority](ARCHITECTURE.md)
and its [Observation boundary](descriptive/OBSERVATION.md).

From the repository root, install the root package with `poetry install --only-root`
after changing source registration. Run Python through `poetry run python`:

```python
from datetime import date

from market_research.descriptive.observation import DateWindow, ObservationJobSpec, observe

# Supply a full canonical index_code confirmed against public index metadata.
job = ObservationJobSpec(
    subject=verified_index_code,
    metric="trailing_cumulative_return_v1",
    metric_parameters={},
    horizon=2,
    historical_sample_window=DateWindow(date(2024, 1, 10), date(2024, 1, 16)),
)
result = observe(job)
```

Inspect `result.candidate_anchors`, `eligible_observations`, `unavailable_observations`
and `excluded_observations`. Each observation has a stable key and anchor; unavailable
observations retain endpoint dependencies and diagnostic reasons. Counts and ratios are
derived properties. `None` ratios mean Not Applicable for zero denominators.

`result.market_fact_coverage` separates `overall`, `warm_up` and `sample`, each with
expected/available/absent keys, counts and a ratio. Legal non-positive closes remain
available facts while causing business exclusions when both endpoints exist.

`result.provenance` retains canonical bytes, `input_fingerprint`, endpoint requirements
and `prepared_inputs`. The latter contains actual Calendar / Index requests, exact final
exports (including original coverage) and every preliminary Export / Ensure attempt.
The digest identifies the consumed v2 inputs; retained facts allow inspection.

For deterministic fixtures or independent pure use:

```python
from market_research.descriptive.cases.trailing_return import (
    construct_observations,
    prepare_inputs,
)

prepared = prepare_inputs(job, calendar_service=calendar_fake, index_service=index_fake)
result = construct_observations(job, prepared)
```

Preparation failures expose `stage`, `category`, `request` and obtained `evidence`;
`UpstreamFailure.__cause__` retains the public DataLake error. An incomplete Calendar
fails preparation; a validated partial Index Export can produce unavailable outcomes.
Construction makes no upstream calls. This API requires no Analyze, Converter or Executor.

Verification commands and actual live-data status are in [Acceptance](descriptive/ACCEPTANCE.md).
