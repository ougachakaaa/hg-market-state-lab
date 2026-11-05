# Research implementation status and validation evidence

This is a non-authority status and evidence record for [Descriptive Research](ARCHITECTURE.md).
Contracts, formulas and workflow semantics remain with their owning documents; ordinary
implementation work starts from the Descriptive entry and the relevant contract, not this
file. Previous stage-by-stage reports and commit sequences remain in Git history. Read this
document for current capability status, release boundaries or the recorded real-market
validation evidence.

## Current status

| Area | Status | Canonical entry |
| --- | --- | --- |
| `trailing_cumulative_return_v1` observation | Implemented; deterministic contract tests; bounded isolated real-market E2E verified | [Observation](OBSERVATION.md), [case](cases/trailing_return/ARCHITECTURE.md) |
| Sample converter | Implemented; deterministic contract tests | [Sample conversion](SAMPLE_CONVERSION.md) |
| Result association | Implemented; deterministic contract tests; observable linkage only, no execution-origin attestation | [Result association](RESULT_ASSOCIATION.md) |
| Single Job executor | Implemented for Index Trailing Return; deterministic contract tests | [Single Job](JOB_EXECUTION.md) |
| ResearchPlan / Batch executor | Implemented; deterministic contract tests | [Batch](BATCH_EXECUTION.md) |
| Capability publication / HTTP entry | One admitted capability; deterministic HTTP acceptance passed; live HTTP not run | [Capability](RESEARCH_CAPABILITY.md), [HTTP contract](../../ui_http/products/research/http-contract.md) |
| Price Segmentation V1 | Implemented as an independent Python observation; isolated real-market E2E verified; not admitted to capability publication, preview, Statistics, HTTP or Workbench | [Price Segmentation](cases/price_segmentation/ARCHITECTURE.md) |
| Publication storage / reader | Implemented; Research Explorer consumes the read-only HTTP delivery | [Publication](../PUBLICATION.md), [storage](../PUBLICATION_STORAGE.md) |
| Individual-stock, futures and other-series cases | Not declared; stock daily public service, adjusted-return policy, futures contract selection and roll semantics remain gaps | [Observation](OBSERVATION.md), [upstream policy](../UPSTREAM.md) |
| Persistence / replay / result cache / CLI / report | Deferred or not implemented | [Deferred scope](ARCHITECTURE.md#deferred-scope) |
| Statistics NumericSample / Quantile / IntervalCount | Independent public Python API implemented; numerical semantics remain Statistics-owned | [Statistics contract](../../market_statistics/CONTRACT.md) |

## Deterministic acceptance scenarios

These are cross-stage acceptance specifications; deterministic coverage is exercised by
the Research test suite. They are not separate business contracts; detailed obligations
remain with the owning contracts and tests.

| Scenario | Fixture and expected behavior |
| --- | --- |
| A — Complete time series | Complete Calendar and legal positive prices: every candidate Eligible; observation coverage 100%, unavailable/excluded ratios 0; verify returns, H, keys, provenance and v2 identity. |
| B — Missing intermediate price | Six open sessions D0..D5, closes [100,110,missing,90,120,130], H=2, anchors D2..D5. D2 Unavailable (anchor D2); D3 Eligible (90/110-1); D4 Unavailable (lookback D2); D5 Eligible (130/90-1). Counts 4=2+2+0; observation coverage 50%, unavailable 50%, excluded 0%; fact coverage 5/6, warm-up 2/2, sample 3/4. Never substitute another date for D2. |
| C — Weekend / holiday | Complete Calendar includes closed dates between opens. Closed dates are neither candidates nor missing Index units; H follows the open-session sequence. No artificial fact-coverage gaps. |
| D — Missing warm-up price | Complete calendar resolves lookbacks, but some required pre-window daily rows are absent under valid proof: affected anchors Unavailable; other computable anchors Eligible; fixed H and independent warm-up fact coverage retained. Unknown history/calendar instead fails preparation. |
| E — Incomplete Calendar | Final Calendar cannot prove full sample/discovery date population: input_preparation fails, no guessed candidate universe or observation coverage; no price-row/weekday inference and no Statistics attempt. |
| F — All market facts missing | Complete Calendar, positive candidate population, valid Index Export with zero success and empty records: all candidates Unavailable, Eligible=0, 0% fact/observation coverage, unavailable ratio 100%. Valid ObservationSet retained; conversion fails NoEligibleObservations, Job Failed, every analysis not_attempted. No successful empty NumericSample. |
| G — Invalid public facts | Wrong scope/schema/identity, duplicate/conflicting/illegal rows or inconsistent coverage: InvalidPublicInput at input_preparation; no silent dropping or ordinary Missing. OperationError is UpstreamFailure, not availability. |
| H — Individual stock capability | Subject abstraction represents stable identity, metric, calendar basis, H/window without changing the general model. Current catalog has no stock daily service; report Upstream Capability Gap and undefined price/adjustment binding, never fake a public API or claim reliable economic returns. |

## Additional implementation gates

| Boundary | Required checks |
| --- | --- |
| Outcome precedence | Two missing endpoints retain two dependencies but one Unavailable. A shared missing fact affects every dependent anchor. Missing plus non-positive endpoint is Unavailable; both available and any non-positive is Excluded non_positive_close, preserving all offending endpoints. |
| Coverage | Non-positive but legal facts count available; positive candidate zero eligible has 0% observation coverage. Zero candidates yield Not Applicable ratios; no-candidate Index not requested. Keep upstream coverage unchanged and Calendar/Index units separate. |
| Public invocation | Export-first; validate partial envelope before ensure; at most one ensure for each incomplete range, then validate final Export. Partial EnsureResult plus valid final partial Index view can construct; OperationError and invalid views fail. Complete final Calendar mandatory. |
| History | One-day sample, adjacent backward doubling, date.min exhaustion, missing Calendar block and legal missing warm-up quotations; no arbitrary cutoff, list_date trimming, suffix guessing or snapshot fallback. |
| Formula / fingerprint | Exact fixtures in case authority; positive-endpoint overflow fails construction; v2 deterministic bytes and sensitivity from identity contract, no-candidate versus empty Index distinction, old v1 not reinterpreted. |
| Converter / association | All Eligible values once in order; preserve equal-valued distinct keys, exact units, missing/excluded records, full coverage/evidence and dependence context; no I/O or second screen. Invalid accounting/unmappable scalar fails. Only NumericSample crosses Statistics boundary. Wrong method/spec/count/unit fails association with raw result preserved. |
| Partial successful Job | Valid partial ObservationSet with at least one Eligible plus all required analyses/associations successful yields Job Success with honest coverage. An analysis failure still fails Job; zero Eligible fails conversion with diagnostics preserved. |
| Plan / Batch | Whole-plan preflight before I/O, exact Cartesian order/identity, required analysis order, no analysis dimension expansion, continue and stop accounting per execution contract. |
| Statistics | Existing owner fixtures for types, empty/non-finite sample, duplicates, immutability, unit, quantile estimator/extreme arithmetic and interval endpoints/count conservation remain required. |
| Live data | Explicit metadata-verified CSI1000 code, dates/H and both method parameters; independently check input pairing/returns, sample/binding, analyses/associations and retained fingerprint through authorized public services. No experiments on real user caches. |

## Real-market validation evidence

Both runs used fresh isolated Dataset storage. Default Dataset caches were not opened,
migrated or repaired. Each result is bounded to its stated scope and does not establish
provider freshness or coverage outside it.

### Index Trailing Return

- 2026-10-27, PASS: `000852.SH` (CSI1000) confirmed through public metadata, H=2,
  inclusive anchor window 2024-01-10..2024-01-16, explicit `metric_parameters={}`.
- Five Eligible observations, zero Unavailable/Excluded; overall Index fact coverage 7/7,
  warm-up 2/2, sample 5/5; observation coverage 5/5.
- Quantiles `0.1 / 0.5 / 0.9` = `-0.008045239512030821 / -0.005683318588033837 / 0.010959089549401701`.
- Interval counts for `[-0.2, 0.0, 0.2]` = `3` and `2`; frequencies 0.6 and 0.4; count conservation 5.
- Input profile `trailing_return_inputs_v2`; fingerprint
  `5bbb52782df680da17036420bdee777b9c3febaf19cd08e8f09c383b8ecf2bfc`.
- Direct Single Job and one-Job Batch both succeeded with two successful analyses.
- Harness: `poetry run python market_research/tests/live_e2e_acceptance.py --live --output <output.json>`.

### Price Segmentation

- 2026-10-31, PASS: explicit `000852.SH` scopes in isolated storage; every calendar date,
  open session, public close, PIP point, segment endpoint and fingerprint was checked by an
  independent oracle.
- Short-scope important points `(index, date, close)` are `(0, 2024-01-08, 5543.5745)`,
  `(2, 2024-01-10, 5512.0686)`, `(3, 2024-01-11, 5611.1149)` and
  `(6, 2024-01-16, 5539.4741)`.

| Scope (inclusive) | epsilon | Calendar | Sessions | Points | Segments | Maximum log error | Fingerprint |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| 2024-01-08–2024-01-16 | 0.005 | 9/9 natural days | 7/7 sessions | 4 | 3 | 0.004603231652222206 | `64b2b9cc9ab212442a248cedd1188c3ba0b372f2404674ba7b7baf09bbc49103` |
| 2024-01-08–2024-02-29 | 0.01 | 53/53 natural days | 33/33 sessions | 21 | 20 | 0.0087081168442662 | `bfc446b97e0422c276920605049651cacb311cf523ec2aa39916b53b3c195095` |

| Start | End | Session intervals | Signed amplitude | Direction | Boundary |
| --- | --- | ---: | ---: | --- | --- |
| 2024-01-08 | 2024-01-10 | 2 | -0.005683318588033837 | down | start |
| 2024-01-10 | 2024-01-11 | 1 | 0.017968988992626 | up | neither |
| 2024-01-11 | 2024-01-16 | 3 | -0.01276765870540264 | down | end |

- Harness: `poetry run python market_research/tests/segmentation_live_e2e.py --live --long --output <output.json>`.

## Operational limits

- Live HTTP acceptance was not performed. Deterministic HTTP acceptance does not establish
  live HTTP readiness.
- The historical default Trade Calendar cache remained incompatible; default-cache recovery
  was not performed. Verified runs used fresh isolated storage.
- No execution persistence/replay/result cache, retry/queue/scheduler, CLI, report
  renderer, Research frontend or Conditional implementation is published; explicit opt-in
  Publication storage is separate.
- Upstream availability, credentials, Calendar completeness and partial Index facts remain
  operational dependencies.
- Price Segmentation remains a Python observation only; it is not admitted to capability
  publication, preview, Statistics, HTTP or Workbench.
- Validation is bounded to the stated scopes and does not establish financial swing quality,
  provider freshness or general market readiness.

### Native Windows Publication limitation

Publication V1 currently depends on POSIX directory descriptors, `dir_fd`,
`O_DIRECTORY` and `O_NOFOLLOW` to enforce the [storage contract](../PUBLICATION_STORAGE.md).
Native Windows lacks these primitives: importing Publication can fail before a
store is opened. Because the combined HTTP app imports Publication delivery, this
also blocks backend startup and Web contract export on native Windows. This
limitation predates the final integration baseline; neither integration source
changes Publication storage. A native Windows runtime has not been validated.

The Windows one-click launcher does not resolve this limitation. Portfolio work
can use a validated Linux runtime (or WSL with the same required filesystem
capabilities); native Windows HTTP integration remains unavailable pending a
separately verified secure implementation. Do not remove no-follow checks or
substitute zero-valued flags to claim compatibility. This integration performs no
live market acceptance or default-cache recovery.
