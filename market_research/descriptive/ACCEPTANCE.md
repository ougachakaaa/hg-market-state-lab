# Descriptive Research verification scope

Current cross-stage verification specifications for the scalar Trailing Return path.
Canonical behavior remains in the linked [Descriptive contracts](ARCHITECTURE.md);
select directly changed cases under the [root verification policy](../../AGENTS.md#verification-policy-user-decision-2026-11-14).
Futures Basis, Calendar Spread and Price Segmentation have independent case contracts
and tests. Test existence is not a claim of a current passing run.

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
