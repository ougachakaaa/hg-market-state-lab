# Market Statistics V1

Pure Python numerical API with NumPy as its implementation dependency. Install from
the repository root with `poetry install`; use the root Poetry environment. The
[module authority](ARCHITECTURE.md) routes to the public and method contracts.

```python
from market_statistics import NumericSample, QuantileSpec, compute

result = compute(
    NumericSample(values=[3, 1, 1, 9], unit="points"),
    QuantileSpec(points=[0, .25, .5, .75, 1]),
)
assert result.points_and_values == ((0, 1), (.25, 1), (.5, 2), (.75, 4.5), (1, 9))
assert result.sample_count == 4
assert result.unit == "points"
```

```python
from market_statistics import IntervalCountSpec, NumericSample, compute

result = compute(
    NumericSample(values=[-1, 0, 1, 1, 2, 3], unit="points"),
    IntervalCountSpec(edges=[0, 1, 2], unit="points"),
)
assert [bin_.count for bin_ in result.bins] == [1, 3]
assert result.underflow_count == result.overflow_count == 1
assert result.sample_count == 6
assert [bin_.frequency for bin_ in result.bins] == [1 / 6, 3 / 6]
assert result.underflow_frequency == result.overflow_frequency == 1 / 6
```

These examples also run independently as
`poetry run pytest market_statistics/tests/test_public_api.py::test_quantile_example -q`
and
`poetry run pytest market_statistics/tests/test_public_api.py::test_interval_count_example -q`.

Samples and specs validate on construction, copy coordinates into immutable binary64
tuples and preserve opaque units exactly. `validate_spec` performs sample-free preflight;
`compute` revalidates sample, spec and compatibility in that order. Results contain
immutable Python values. Invalid requests raise `InvalidSample` or
`InvalidStatisticalSpec`; numerical failures raise `CalculationFailure` with `method`,
`reason` and an original cause where available. All belong to `StatisticalFailure`.

NumPy 2.5.3 on Python 3.13 is the tested backend. Quantile's frozen binary64 adaptation
is explained in [BACKEND.md](BACKEND.md); the statistical contracts are unchanged.
The deterministic suite covers public legality, both methods, backend failure injection,
isolated installed imports and architecture boundaries. Research Converter, result
association and Job / Batch Executor remain outside this implementation; prior blocked
live-data acceptance remains unchanged.

## STAT-IMP-01 verification (2026-10-25)

Baseline: `eb86786527889f25f4879484d78da2f58e22c3eb`, branch
`reset/market-research-descriptive`, clean worktree before implementation.
The existing numerical contracts and Research/Statistics ownership are unchanged;
only runtime readiness statements, package/tool registration and backend implementation
evidence were reconciled. No unresolved contract deviations were found.

| Executed command / check | Result |
| --- | --- |
| `poetry install --only-root` | Passed |
| `poetry check --lock` | Passed; NumPy remains locked at 2.5.3 with a new direct declaration |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest market_research/tests -q` | 192 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 19 passed |
| `poetry run ruff check market_statistics market_research ui_http data_snapshot/tests/test_authority_topology.py` | Passed |
| `poetry run mypy market_statistics/src market_statistics/tests market_research/tests data_snapshot/tests/test_authority_topology.py ui_http` | Passed; 42 source files |
| `poetry run pytest -q` | 1510 passed; one existing FastAPI/Starlette TestClient deprecation warning |
| Root wheel build and isolated installed public imports | Passed |
| `git diff --check` and full change review | Passed |

All requested Statistics checks executed. Historical Observation/DataLake live-data
acceptance remains blocked as previously recorded in the
[Research acceptance evidence](../market_research/descriptive/ACCEPTANCE.md);
this purely numerical implementation makes no live-data acceptance claim.
