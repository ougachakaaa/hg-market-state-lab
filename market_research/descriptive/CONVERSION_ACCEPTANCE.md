# CONV-01 implementation evidence

This is the converter-specific verification and reconciliation record reached from
[Acceptance](ACCEPTANCE.md). Semantic obligations remain exclusively in
[Sample conversion](SAMPLE_CONVERSION.md); this record publishes no second contract.

## Baseline and sequential delivery

On 2026-10-26 the actual branch was `reset/market-research-descriptive`, HEAD was
`5c10e4e871c9540c04e36941a5f5adb93bd44a2f` and the worktree was clean, matching the request.
Observation Producer and Statistics V1 existed. Converter, Result Association and
Job/Batch Executor did not. No baseline reconciliation or unrelated-work preservation
was necessary. No market caches were accessed or changed.

Authority commit `2d4755c` (`docs(research): freeze descriptive sample conversion authority`)
preceded all converter runtime changes. It split conversion from Statistics integration,
updated navigation and added the topology entry. Runtime commit `df75c58`
(`feat(research): implement descriptive observation sample converter`) implements that
authority with no new semantic decision, dependency, package registration or Statistics
API change. The final documentation commit records readiness, usage and this evidence.

## Canonical runtime model

The public facade is `market_research.descriptive.conversion`, exporting `convert`,
`SampleProjection`, `SampleBinding`, `InvalidObservationSet`, `NoEligibleObservations`
and `UnmappableSample` through explicit aliases without `__all__`.

`convert(ObservationSet[P]) -> SampleProjection[P]` returns frozen carriers:

```text
SampleProjection[P](numeric_sample: market_statistics.NumericSample, binding: SampleBinding[P])
SampleBinding[P](source_observation_reference: ObservationSet[P],
                 ordered_observation_keys: tuple[ObservationKey, ...])
```

Binding counts, unavailable/excluded records, coverage, ratios, provenance and dependence
are typed read-only properties over the actual source. Public Observation validation is
reused after checking required shapes. Request revalidation creates a shallow new request
because its constructor replaces the parameter mapping; the original remains untouched.
No provenance schema is inferred: exact source retention preserves concrete case evidence.
Illegal Observation coordinates are InvalidObservationSet; a present unit rejected by
Statistics is UnmappableSample. A missing unit field is structural invalidity. Error
precedence and original translated causes are tested.

## Deterministic numerical demonstration

An independent `poetry run python -` session used the existing public fixture
`pure_fixture()` with `construct_observations`, then public `convert` and `compute`.
The fixture is explicit `000001.SH`, not a live metadata-verified CSI1000 claim.
Closes [100,110,121,110,121], H=2 produce:

```text
values = (0.20999999999999996, 0.0, 0.0)
sample_count = 3; unit = decimal_ratio
J = (trailing_cumulative_return_v1, 000001.SH, (), 2, trading_sessions,
     2024-01-10, 2024-01-12, end_session, inclusive)
ordered keys = ((J, 2024-01-10), (J, 2024-01-11), (J, 2024-01-12))
counts: candidate=3, eligible=3, unavailable=0, excluded=0
coverage: observation=1.0, overall=1.0, warm_up=1.0, sample=1.0
input_profile = trailing_return_inputs_v2
input_fingerprint = efa5761473299174f411a1cdb35a48bf61e7a5a13a50daaf8a9ac946cdced5ae
Quantile(points=[0, .5, 1]): ((0.0, 0.0), (0.5, 0.0), (1.0, 0.20999999999999996))
IntervalCount(edges=[-.2, 0, .2]): bin counts=(0, 2), underflow=0, overflow=1
bin frequencies=(0.0, 0.6666666666666666), overflow_frequency=0.3333333333333333
```

Both results report count 3 and decimal_ratio and use the same projected sample/binding.
Scenario B independently verifies 4=2+2+0, D3/D5 values, observation coverage 2/4,
overall 5/6, warm-up 2/2 and sample 3/4, with every missing reference/diagnostic retained.
These are deterministic tests and public numerical results, not associated Research Evidence.

## Executed verification

Commands ran from the repository root's unique Poetry environment. Final results:

| Exact command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | 248 passed; 56 added converter/boundary cases |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 19 passed |
| `poetry run ruff check market_research market_statistics` | Passed |
| `poetry run mypy market_research/src market_research/tests` | Passed, 24 source files |
| `poetry run pytest -q` | 1566 passed, one existing Starlette TestClient/httpx deprecation warning |
| `poetry check --lock` | Passed |
| `poetry install --only-root` | Passed |
| `poetry run python -c "from market_research.descriptive.conversion import convert, SampleBinding, SampleProjection, InvalidObservationSet, NoEligibleObservations, UnmappableSample; print('Installed conversion facade: importable')"` | Passed after root installation |
| `poetry run python -` | Independent fixture/public API demonstration above |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py market_research/tests/test_boundaries.py -q` | 22 passed before authority commit |
| `poetry run ruff check data_snapshot/tests/test_authority_topology.py` | Passed |
| `poetry run mypy data_snapshot/tests/test_authority_topology.py` | Passed |
| `git diff --check` and `git diff --cached --check` | Passed; complete authority and implementation diffs reviewed |

Earlier iterations had formatting/type-check findings that were corrected before the
final checks. The full suite was rerun after the final structural regression test.
Markdown navigation/link checks run through the topology suite. The new facade is
importable after root installation; no legacy namespace or generic converter framework
was introduced. Statistics source/contracts, dependency manifest and lock are unchanged.

## Authority/runtime reconciliation

| Concern | Authority requirement | Runtime evidence | Status |
| --- | --- | --- | --- |
| Public convert API | One scalar converter, one concrete binding | [Facade](../src/market_research/descriptive/conversion/__init__.py), test_public_facade_attributes_without_all | Pass |
| Numeric projection | Every Eligible once, unchanged binary64/unit | [Acceptance tests](../tests/test_sample_conversion.py): A, C, D, other scalar case | Pass |
| Positional binding | Keys align with values | A, B, C, J ordered assertions | Pass |
| Population conservation | Candidate = E+U+X | A, B, D, E | Pass |
| Source identity | Actual originating ObservationSet/fixed request | A, H, I reference assertions | Pass |
| Provenance | Original typed fingerprint/profile/inputs/diagnostics | A, B, multiple_missing_dependencies, other typed provenance | Pass |
| Coverage | Original coverage, public proofs and ratios retained | A, B, E (Not Applicable) | Pass |
| Failures | Three categories with precedence and causes | E, F, G, missing_unit_field | Pass |
| Immutability | Pure operation, stable source and carriers | I plus frozen models and no effectful imports | Pass |
| Boundary | Only Statistics public sample edge | [Architecture checks](../tests/test_conversion_boundaries.py), existing Observation API boundary check | Pass |

No authority/runtime drift or unresolved semantic issue remains for this scalar scope.
Structural validation does not reconstruct market facts or prove a new fingerprint.
No new import permission is granted to acquisition/Observation layers. Dependence remains
original context; no independence claim is added.

## Current readiness and remaining gates

| Delivery component | Status |
| --- | --- |
| Observation Producer | Implemented |
| Statistics V1 | Implemented |
| Sample Converter | Implemented |
| Result Association | Not Implemented — Pending |
| Research Job Executor | Not Implemented — Pending |
| Research Batch Executor | Not Implemented — Pending |
| Live Market End-to-End Research | Pending |

The [historical live Observation gate](ACCEPTANCE.md#verification-evidence-2026-10-25)
remains blocked by the incompatible Trade Calendar cache recorded there. CONV-01 did
not rerun live acquisition, verify CSI1000 metadata, rebuild caches or resolve that runtime
state. No live end-to-end Research acceptance is claimed. Result Association, Job/Batch
execution and live Research remain separate goals. CONV-01 Complete.
