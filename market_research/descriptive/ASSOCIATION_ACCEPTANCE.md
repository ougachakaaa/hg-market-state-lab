# ASSOC-01 implementation evidence

This is the factual association verification/reconciliation record reached through
[Acceptance](ACCEPTANCE.md) and [Statistics integration](STATISTICS_INTEGRATION.md).
Semantic obligations belong exclusively to [Result Association](RESULT_ASSOCIATION.md).
This record is not a competing contract. Verification date: 2026-10-26.

## Baseline and sequential delivery

Actual branch: `reset/market-research-descriptive`. HEAD was the exact required baseline
`c57ac575c68dd47331c8b6ddc6dbb78066f49795`; the worktree was clean. Observation Producer,
Converter and Statistics V1 were implemented; Association and Job/Batch Executors were
absent. No advanced-HEAD reconciliation, reset or unrelated-work discard was required.
Baseline `poetry run pytest market_research/tests market_statistics/tests -q` passed
419 tests. No market caches or live acquisition were used.

| Sequence | Commit | Scope |
| --- | --- | --- |
| 1 | `5ba58d2b96cf005abc09841bc729bd65dec4473d` — docs(research): freeze statistical result association authority | Authority/navigation and topology entry only; runtime remained Not Implemented |
| 2 | `454d9b42f9d4bb12cc675c041541eb59fdaa7463` — feat(research): implement statistical result association | Public models/operation/failure, deterministic tests and precise boundary permissions |
| 3 | This record's commit — docs(research): reconcile statistical result association implementation | Factual readiness, usage, navigation and reconciliation only |

The integration entry routes to the independently consumable association contract;
conversion and execution retain separate ownership. Runtime implements the committed
decisions without an intervening semantic change. Statistics source/contracts,
dependency manifest/lock, Observation and Converter source are unchanged.

## Public runtime model

```python
from market_research.descriptive.association import (
    AnalysisRequest, ResearchAnalysisEvidence, ResultAssociationFailure, associate,
)
```

Actual frozen dataclass fields:

```text
AnalysisRequest(request_id: str, spec: market_statistics.StatisticalSpec)
ResearchAnalysisEvidence[P](request: AnalysisRequest,
    statistical_result: market_statistics.StatisticalResult, projection: SampleProjection[P])
```

The evidence read-only `source_observation_reference` follows its original binding.
Successful association retains exact request, spec, result, projection, sample, binding,
source and typed provenance objects. A separately constructed structurally equivalent
fixed Job is legal; the source's original fixed Job remains retained. Direct evidence
carrier construction does not establish validated association; use `associate`.

Source checks use public Observation invariants after bounded shape checks. Fixed request
revalidation constructs a shallow new request because its constructor replaces its parameter
mapping; the original mapping is untouched. Public NumericSample construction checks
numerical legality without replacing the original sample. Public validate_spec checks
requests at construction and association. No private Statistics/Converter validator or
case-specific provenance schema is imported. Result checks inspect parameters, finite
payload shape, bin geometry and retained count/frequency accounting without recalculating
Type 7 or sample membership. No mathematical-origin guarantee is claimed.

## Independent public numerical demonstration

A standalone `poetry run python -` process imported only `pure_fixture` from the existing
test-fixture directory, then used installed public construction, conversion, Statistics and
Association facades. No production source path was injected. The same chain is executable
in `test_a_public_component_chain_retains_exact_objects_and_complete_context` in the
[acceptance tests](../tests/test_result_association.py).

```python
fixed_job, prepared_inputs = pure_fixture()
observation_set = construct_observations(fixed_job, prepared_inputs)
projection = convert(observation_set)
request = AnalysisRequest("return_quantiles", QuantileSpec([0, 0.5, 1]))
statistical_result = compute(projection.numeric_sample, request.spec)
evidence = associate(fixed_job, observation_set, projection, request, statistical_result)
```

Actual complete synthetic fixture output (not a live metadata-verified CSI1000 claim):

```text
closes = [100,110,121,110,121]; H = 2
J = (trailing_cumulative_return_v1, 000001.SH, (), 2, trading_sessions,
     2024-01-10, 2024-01-12, end_session, inclusive)
ObservationSet: candidate=3, eligible=3, unavailable=0, excluded=0
SampleProjection.numeric_sample:
    values = (0.20999999999999996, 0.0, 0.0), count=3, unit=decimal_ratio
SampleProjection.binding.ordered_observation_keys:
    ((J, 2024-01-10), (J, 2024-01-11), (J, 2024-01-12))
request_id = return_quantiles; QuantileSpec.points = (0.0, 0.5, 1.0)
QuantileResult:
    points_and_values = ((0.0,0.0), (0.5,0.0), (1.0,0.20999999999999996))
    method=quantile, estimator=type7_linear_v1, count=3, unit=decimal_ratio
ResearchAnalysisEvidence(request=request, statistical_result=statistical_result,
                         projection=projection)
    request/result/projection/source/prepared_inputs identity assertions all passed
input_profile = trailing_return_inputs_v2
input_fingerprint = efa5761473299174f411a1cdb35a48bf61e7a5a13a50daaf8a9ac946cdced5ae
coverage: observation=1.0, overall=1.0, warm_up=1.0, sample=1.0
dependence spans: Jan10 <- Jan08, Jan11 <- Jan09, Jan12 <- Jan10
    original overlapping/shared-endpoint interpretation retained
```

The same projection served a second request `return_distribution`:

```text
IntervalCountSpec: edges=(-0.2,0.0,0.2), unit=decimal_ratio
IntervalCountResult: method=interval_count, sample_count=3, unit=decimal_ratio
bins: [-0.2,0.0) count=0 frequency=0.0; [0.0,0.2] count=2 frequency=0.6666666666666666
underflow_count=0, overflow_count=1
underflow_frequency=0.0, overflow_frequency=0.3333333333333333
second Evidence: distinct request/result, identical projection/binding/sample/source
```

Partial fixture `[100,110,missing,90,120,130]`, H=2 passes with 4=2+2+0,
Eligible D3/D5, observation coverage 2/4, fact coverage 5/6, warm-up 2/2 and sample 3/4.
All unavailable dependency objects and original public coverage/provenance are retained.
Mixed unavailable/excluded populations retain reasons and offending facts. Another typed
scalar provenance with no fingerprint field passes both methods without a case subclass.

## Negative and limitation evidence

Dedicated tests reject changed Job horizon/window/subject/metric/parameters, a projection
bound to another equal-valued source object, wrong/missing public carriers, dropped or
reordered/duplicated keys, mismatched exact values/signed zero, count and unit mismatches.
They reject crossed Quantile/IntervalCount variants, changed/reordered/missing/extra
points, wrong estimator/method, changed edges/order, malformed bins/closures, bool or
negative counts, broken conservation, illegal/inconsistent frequencies and missing fields.
Request IDs remain exact, including whitespace; invalid construction and malformed boundary
requests have their separate promised failures. Safe attribution and exception causes
are tested. A real raw result remains unchanged and can subsequently associate successfully.

`test_n_metadata_cannot_attest_hidden_computation_origin_or_numerical_correctness`
accepts distinct metadata-identical results, a structurally legal finite Quantile payload
and an unrelated computed histogram with legal geometry/accounting. This explicitly
demonstrates the limit: bare results do not identify their sample or authenticate their
computation history. Positive acceptance uses actual corresponding public compute results.
Future Executor must pass its corresponding result directly; no attestation/hash protocol
is introduced.

Purity tests actively block file open, socket creation, SQLite connect, public DataLake
factories/services, compute, convert and construction/preparation during success and
failure. Input snapshots and original mappings/references remain unchanged; evidence and
request assignments raise FrozenInstanceError. AST negative checks separately prohibit
effectful dependencies, private imports, reverse/converter-to-association dependencies,
Executor imports and Statistics computation from Association.

## Executed verification

All commands ran locally from the repository root in its unique Poetry environment;
these results are not a CI claim.

| Exact command | Actual final result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | 439 passed; 174 association cases and 17 additional negative boundary cases beyond the 248-test baseline |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 19 passed |
| `poetry run ruff check market_research market_statistics` | Passed |
| `poetry run mypy market_research/src market_research/tests` | Passed; 31 source files |
| `poetry run pytest -q` | 1757 passed; one existing Starlette TestClient/httpx deprecation warning |
| `poetry check --lock` | Passed |
| `poetry install --only-root` | Passed |
| `poetry run python -c "from market_research.descriptive.association import AnalysisRequest, ResearchAnalysisEvidence, ResultAssociationFailure, associate; print('Installed association facade: importable')"` | Passed after root installation |
| `poetry run python -` | Standalone installed public API demonstration above, both methods |
| `poetry run python -` (local Markdown link/anchor audit) | Passed; 137 local links/anchors across 11 changed Markdown files |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py market_research/tests/test_boundaries.py -q` | 22 passed before Authority commit |
| `poetry run ruff check data_snapshot/tests/test_authority_topology.py` | Passed before Authority commit |
| `poetry run mypy data_snapshot/tests/test_authority_topology.py` | Passed before Authority commit |
| `poetry run ruff check data_snapshot` | Passed |
| `poetry run mypy data_snapshot` | Passed; 64 source files |
| `poetry run mypy market_statistics/src market_statistics/tests` | Passed; 14 source files |
| `git diff --check` / `git diff --cached --check` | Passed; full Authority and runtime diffs reviewed before sequential commits |

An initial targeted run had 2 failed / 189 passed: the test used `success_units` instead
of public `successful_units`, and attempted repr on a deliberately field-deleted sample.
Both test harness errors were corrected; final module and full-suite results above pass.
Initial Ruff import/line formatting findings were fixed before final lint/type checks.
The first ad hoc link audit misread a fenced generic type signature as a Markdown link;
excluding fenced/inline code from link extraction resolved that audit error. The final
topology/link suite was also rerun after completion documentation and passed 19 tests.
No Statistics algorithm/source was changed to obtain these results.

## Authority-to-runtime reconciliation

| Concern | Verification evidence | Status |
| --- | --- | --- |
| Public API | One installed facade; explicit aliases, no __all__; public component chain | Pass |
| AnalysisRequest | Exact ID/spec objects, public validation at both boundaries, distinct occurrences, local/boundary error tests | Pass |
| Evidence | Frozen three-field composition; original request/result/projection/source and typed references | Pass |
| Quantile | A/H: exact points/order, estimator, method, finite shape, count/unit checks | Pass |
| IntervalCount | B/I: exact edges, bin geometry/closures, retained count/frequency accounting | Pass |
| Source identity | E: structural fixed Job equivalence, parameter-name order, actual bound source identity | Pass |
| Provenance | A/D/M: original typed evidence, input profile/fingerprint, public facts; no universal schema | Pass |
| Coverage | D and mixed-source tests: unavailable/excluded records, observation/fact/warm-up/sample context retained | Pass |
| Failure | Wrong/malformed inputs and L: stage/category/reason, safe optional attribution and causes | Pass |
| Raw result | L: same unchanged real result after failure, then successful association | Pass |
| Purity | K plus precise negative AST checks: no I/O, conversion, acquisition or statistics recomputation | Pass |
| Dependencies | Observation/Converter boundaries preserved; Association public facades only; Statistics reverse dependency checks pass | Pass |
| Numerical execution-origin authentication | Deliberately outside contract; N proves observable metadata cannot establish hidden origin | Not Verified — explicitly not guaranteed |
| Live Research E2E | No live acquisition or cache modification; historical calendar limitation retained | Remaining Gap |
| Job/Batch execution, persistence/cache | Not implemented or claimed by this goal | Remaining Gap — deferred scope |

No Authority/runtime deviation remains in ASSOC-01's published scalar association scope.
The old conversion-only architecture-test absence gate is replaced by precise Association
permissions and negative tests; the conversion contract's test-status description is updated.
Historical OBS/CONV evidence retains its original phase status; current readiness is below.

## Readiness and remaining roadmap

| Component | Current status |
| --- | --- |
| Observation Producer | Implemented |
| Sample Converter | Implemented |
| Statistics V1 | Implemented |
| Result Association | Implemented |
| Single Job Executor | Not Implemented — EXEC-01 |
| Batch Executor | Not Implemented — EXEC-02 |
| Research Evidence Storage | Not Implemented — Deferred |
| Result Reuse / Cache | Not Implemented — Deferred |
| Live Research E2E | Pending |

The [historical Trade Calendar cache limitation](ACCEPTANCE.md#verification-evidence-2026-10-25)
is unchanged; this goal neither reran live acquisition nor repaired caches or verified
CSI1000 metadata. EXEC-01 — Single Job Executor, EXEC-02 — Research Batch Executor,
Live Research E2E Acceptance, and Evidence Persistence / Result Reuse remain separate
roadmap work. ASSOC-01 Complete; no Executor implementation is started.
