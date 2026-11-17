# Daily futures–spot comparison authority

This Daily-only contract specializes the [case](ARCHITECTURE.md) and is independent
of the six calendar-spread pairs in [Definition](DEFINITION.md). Definition identity:
`daily_futures_spot_definition_v1`. It creates no historical observation population.

## Inputs and financial definition

Reuse the completed Daily day's Slot resolution, validated FuturesDailyRows and
same-result [underlying index reference](DAILY_INDEX_REFERENCE.md). Never resolve
again, acquire another quote, align to another date or substitute a continuous contract.
Only M0, M1, Q1, Q2 are compared, in that order. CFFEX closed days have no comparisons;
SSE closure independently makes the index reference not applicable.

For each selected real contract, F is its same-day Close, S is underlying_index.close,
and D is (actual delist_date - query trade_date).days. D must be nonnegative.
Prices must be built-in int/float (not bool), finite binary64 and strictly positive.

```text
signed_spread = F - S                         # index_points
annualized_point_spread = (F - S) * 365 / D    # index_points_per_365_natural_days
annualized_spread_ratio = 365 * ln(F / S) / D  # decimal_ratio
```

Use precisely this binary64 operation order, checking every executed intermediate
and result. No rounding, epsilon, clamping, algebraic rewrite or fallback is allowed.
For D=0, compute only the point spread; both annualized metrics are null. These
annualizations describe prices, not achievable holding returns. The existing expiry
stages 0_7 / 8_21 / 22_plus apply to D without changing historical groups.

## Outcomes, precedence and evidence

Open days always contain four formal items, including unavailable items. Precedence:

| Condition | outcome | reason | failure_category | Metrics |
| --- | --- | --- | --- | --- |
| No resolved active contract | not_applicable | no_active_contract | null | all null |
| Reference not available | not_applicable | index_reference_unavailable | reference category | all null |
| Either Close <= 0 | excluded | nonpositive_close | null | all null |
| Numerical overflow, nonfinite intermediate, ratio underflow or illegal log | error | calculation_failure | calculation_failure | all null |
| Legal prices and D=0 | not_applicable | expiry_day | null | point spread only |
| Legal prices and D>0 | valid | null | null | all three |

Illegal types, nonfinite input, negative D, wrong identity/date or missing resolved
quote are input-contract defects, not repaired outcomes. Existing upstream validation,
Slot resolution and six-pair whole-query failures remain binding. Only new period-to-
spot numerical failures are isolated per item; other valid results remain intact.
Retain exact underlying reference availability/reason/category separately, with original
Daily reference evidence and Slot universe evidence. Numerical failure evidence retains
a safe code and associated exception internally, never raw exception text in HTTP.

[Query Results](QUERY_RESULTS.md) owns immutable carriers; HTTP projects them without
calculating or reclassifying. Frontend and exports never calculate financial values.
