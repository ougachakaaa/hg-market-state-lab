# Descriptive implementation acceptance authority

This document specializes the [Descriptive entry](ARCHITECTURE.md). It owns readiness
gates and cross-contract verification obligations, not competing numerical, financial
or execution semantics. Detailed deterministic fixtures live with their semantic owners.
Implementation Ready means implementation needs no additional business decisions;
it never means an executable API or real-data acceptance already exists.

## Readiness matrix

| Work package | Semantic status | Canonical decision and test owner | Runtime status |
| --- | --- | --- | --- |
| Analyze | Implementation Ready | [Sample/API/errors](../../market_analyze/CONTRACT.md), [Quantile](../../market_analyze/QUANTILE.md), [IntervalCount](../../market_analyze/INTERVAL_COUNT.md) | No package or installed API |
| Observation | Implementation Ready for first scalar case | [OBSERVATION.md](OBSERVATION.md), [case specialization](cases/trailing_return/ARCHITECTURE.md) | No producer |
| Converter / association | Implementation Ready | [ANALYZE_INTEGRATION.md](ANALYZE_INTEGRATION.md) | No converter/association |
| Single Job / Batch | Implementation Ready | [EXECUTION.md](EXECUTION.md) | No executors |
| First Trailing Return case | Implementation Ready with caller-supplied canonical index_code | [Case authority](cases/trailing_return/ARCHITECTURE.md) | No runtime; actual CSI1000 identity/data acceptance remains unperformed |

Readiness does not cover new metrics, Conditional, new sample shapes, optional analyses,
retries or durable outputs. Required dates/code/method parameters are inputs, not unresolved
semantic defaults. The live-data gate must verify the actual CSI1000 code; a guessed code
is not evidence.

## Implementation test matrix

| Boundary | Success / boundary tests | Explicit failure tests |
| --- | --- | --- |
| Analyze API | Singleton, duplicates, immutability, unchanged unit; typed output/derived count | Invalid shape/type, non-finite/bool, empty, unknown tag, revalidation, precedence |
| Quantile | Owner's exact Type 7 fixtures, endpoints, singleton, repeated values | Illegal points/order; exact extreme-arithmetic CalculationFailure fixture |
| IntervalCount | Every endpoint, single bin, outside categories, total-count conservation | Invalid edges/unit; sample/spec unit mismatch |
| Observation | One outcome per candidate, unique ordered keys, count conservation | Required upstream gaps fail preparation; malformed construction fails |
| Converter | All eligible values once, key/value bijection, units/exclusions/provenance retained | Empty eligibility, malformed accounting, unmappable scalar; no hidden filter/I/O |
| Association | Subject/metric/horizon/window, request/spec, binding/result retained | Wrong method/parameters/count/unit fails association without recomputation |
| Plan / Job | Cartesian order, stable identity, all required analyses tried, one reused sample | Whole-plan preflight before I/O, duplicate IDs/dimensions, per-stage failures/not_attempted |
| Batch | Owner's S/F/S continue and S/F/Skipped stop fixtures; full ordered totals/status | Failed never Skipped, triggering Job retained, no all-skipped valid execution |
| Case binding | Fake public services verify exact requests, backward warm-up, final export proof | Incomplete/invalid view, unit/operation failure, missing history; no Snapshot/private access |
| Case formula / provenance | Owner's session-return fixtures, exclusions, empty population, canonical hash | Illegal required facts, overflow, identity mismatch; no name-based code guessing |
| Real data end to end | Case owner's explicit-code acceptance: complete facts, independently checked returns, both analyses/associations, retained fingerprint | No success from partial facts or unknown instrument identity |

Pure Analyze tests need no upstream services. Research tests may isolate with public-contract
fakes; integration acceptance must exercise actual Analyze public objects/errors once
implemented. Live acceptance uses authorized services and explicit inputs, not provider
clients or experiments on user caches. Statistical runtime tests cannot be claimed passed
before implementation.

## Reconciliation and handoff

The former generic statistical/dependence context in NumericSample is replaced by a narrow
numerical coordinate plus Research-owned binding. Observation request identity is distinct
from analysis requests and actual input revisions. The former direct converter return is
refined to SampleProjection; only numeric_sample crosses Analyze's boundary. Pending
estimator, interval, population, expansion and failure-policy placeholders are replaced
by the linked contracts, not retained as alternate rules.

No upstream service or frozen DataLake invariant changes. A complete-but-empty Calendar
window can produce a valid zero-candidate ObservationSet and explicit conversion failure.
Complete public finite but non-positive prices are separated from missing/illegal facts
by case eligibility. Each operation retains its own proof; no cross-Dataset transaction
or freshness is promised.

Absent Research/Analyze runtime, package registration, CLI/API and behavior tests are
Expected Implementation Gaps. Retired interfaces remain retired. Conditional remains
independent, without scaffold/import path. There is no remaining required Semantic Gap
in this encoded first-case scope. Tooling gaps must be reported from actual verification;
architecture checks establish structure, not statistical or live-data correctness.
