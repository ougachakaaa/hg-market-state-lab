# WP4 descriptive statistics acceptance

Evidence for [Case](ARCHITECTURE.md); contracts remain in [Statistics scope](STATISTICS.md),
[typed analysis API](STATISTICS_API.md) and Statistics-owned [Mean](../../../../market_statistics/MEAN.md).

WP4 **PASS**, 2026-11-06. Branch `feat/r01-futures-basis-research`, baseline
`cc4c4f0212ffd72d356f6476418e7285f56818e7`. One independent WP4 commit, no develop merge.

## Implemented boundary and reconciliation

Statistics adds parameterless MeanSpec and typed MeanResult, facade exports, union,
validation and NumPy float64 backend. Intermediate overflow, nonfinite/malformed
outputs and numerical warnings fail as CalculationFailure without method substitution.
Quantile and IntervalCount semantics are unchanged. No business imports, registry,
grouped/paired/temporal sample or new dependency is introduced.

Research adds explicit DistributionRequest/ComparisonRequest and analyze_distribution,
compare_terms, discount_runs. Original request IDs, specs, numerical results and full
WP3 source objects remain associated. Bindings retain ordered Slot-day objects,
Contract-days, definition, input fingerprint and source evidence. Candidate collections
preserve reasons and allow per-window accounting; source retains independent coverage
proofs and base/metric accounting. Histogram frequencies are Statistics-owned.
Empty eligibility never reaches Statistics. Statistical failures retain public category;
association failures retain the raw returned object and explicit failure status.

Only the Case statistics adapter is admitted to the root Statistics facade in the
architecture checks. Existing scalar Horizon/converter/Job/Batch and Trailing Return
semantics remain unchanged; their association still supports its original methods.
WP5 can consume these frozen outputs directly for projection/reporting.

## Synthetic and numerical acceptance

Mean fixtures check ordinary/singleton/duplicate/cancellation values, units, immutable
inputs, extreme intermediate overflow, spec revalidation and injected malformed,
nonfinite, out-of-range and warning/exception backend failures.
Case fixtures check all three populations, order/multiplicity, expiry loss, method
and result object identity, histogram conservation, six pairs per metric, empty and
disjoint intersections, complete/censored runs, sign termination, all ineligible gap
categories, contract transitions, weekends, narrow/empty windows, no empty numerical
calls, failure association and untouched inputs. WP2/WP3 and existing cases regress.

Verification: the combined required suite passed **1421 tests** before the final
scalar-association regression was added; the affected association/boundary subset
then passed **409 tests**. Ruff, MyPy of all Statistics and Research source/tests, topology and
architecture checks, relative links and `git diff --check` passed.

Reproduce required gates from repository root:

```bash
poetry run pytest -q market_statistics/tests market_research/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_statistics market_research data_snapshot/tests/test_authority_topology.py
poetry run mypy market_statistics/src market_statistics/tests market_research/src market_research/tests data_snapshot/tests/test_authority_topology.py
git diff --check
```

## Retained real IM acceptance

**PASS** using the original WP3 public-service caches in a new isolated external copy,
with Source preparation forbidden. Canonical input bytes match exactly. No acquisition,
synthetic substitution or default cache modification occurred.

Scope: IM / `000852.SH`, `2026-10-12..2026-10-23`. Input SHA-256:
`6facf8378a576eb914e8675dfa0d0c8ee54be356e21cabdc7c40d52bdce27154`.
Calendar coverage is 12/12 natural dates on each exchange, Futures 10/10 product-days,
Index 10/10 sessions. There are 10 candidate sessions × four Slots; raw metrics have
40 eligible observations, annualized has 39 eligible plus one expiry Not Applicable.
No unavailable/excluded rows occur. These unlike coverage units are never summed.

All 12 Slot/metric distributions contain explicit Mean, Quantile points
`[0,.25,.5,.75,1]` and explicit IntervalCount edges. Edges are:

- `basis_value`: `[-1000,-500,-100,0,100,500,1000]` index_points.
- `basis_ratio`: `[-1,-.1,-.01,0,.01,.1,1]` decimal_ratio.
- `annualized_basis_ratio`: `[-10,-1,-.1,0,.1,1,10]` decimal_ratio.

| Slot | Basis mean (points) | Ratio mean (decimal) | Annualized mean (decimal) | Eligible raw / annualized |
| --- | --- | --- | --- | --- |
| M0 | -19.01426 | -0.00284034368249 | -0.0591829558029 | 10 / 9 |
| M1 | -75.07426 | -0.0111008458979 | -0.0844525798447 | 10 / 10 |
| Q1 | -184.79426 | -0.0273615029952 | -0.0935292142928 | 10 / 10 |
| Q2 | -350.37426 | -0.0517611575387 | -0.0977958711709 | 10 / 10 |

All 18 pair/metric comparisons use independently checked common-date intersections.
Raw comparisons have 10 dates; annualized M0 pairs have 9, excluding 2026-10-16.
Other annualized pairs have 10. No calendar spread is calculated.

Independent Decimal summation verifies M0 basis mean `-19.014260000000103`.
Independent ordered Type-7 calculation verifies its five quantiles:
`[-63.0598,-45.452675,-17.29765,5.04065,34.0556]` (display rounded).
M0 has two complete runs and one censored five-session fragment. M1/Q1/Q2 each
have a ten-session censored fragment; transitions do not terminate those spans.
Censored lengths are observed lower bounds, never complete duration estimates.

External artifacts: `/tmp/hg-market-state-lab-wp4-im-20261106-accepted/acceptance.json`,
`results.json` and isolated Dataset copies. Full statistical payloads, counts,
frequencies, requests, method parameters and exact source/binding objects are retained
outside Git. These disposable files require external preservation for longer retention.

Offline replay (choose a nonexistent external output directory):

```bash
poetry run python market_research/tests/futures_basis_statistics_acceptance.py --wp3 /tmp/hg-market-state-lab-wp3-im-20261106 --output /tmp/hg-market-state-lab-wp4-im-repeat
```

This is test infrastructure, not a public serialization API. It requires the retained
WP3 caches and canonical bytes; the public workflow is the [Python example](USAGE.md).
Slots share dates and underlying prices. This short window validates E2E behavior and
supports no long-term market-state, independent-sampling or predictive conclusion.
WP5 visualization/offline packaging remains unimplemented and does not reduce WP4 PASS.
