# Date-axis research chart presentation authority

This is the single authority for how a research surface presents a date x-axis. It
specializes the [presentation architecture](presentation-architecture.md) and applies
the renderer options owned by the [Visualization contract](VISUALIZATION.md) and the
[V2 date-series contract](VISUALIZATION_V2.md). It owns the repository-wide
`Trading Days` / `Calendar Days` presentation policy only; producer Views, business
semantics, financial values and feature series/axis/visual encoding stay with their
owning authority.

## 1. Applicability and exceptions

Apply this policy when both hold:

- the x axis is a date coordinate expressing a time-ordered research or backtest series;
- the owning result (or an explicitly authorized data source) supplies an authoritative
  ordered trading-session domain for the displayed marks and events.

Current applications are the W1 historical basis charts and the W2 cumulative return
and drawdown charts. New applicable charts must be added to §7.

Do **not** apply this policy, and never infer a market calendar, when:

- the data are natural-day data with no trading-session concept;
- no authoritative trading-session domain exists for the displayed marks/events;
- the x axis is not a date (histogram category, strike, count, probability, numeric);
- the surface is a generic published-View reader that has no session domain for an
  arbitrary publication.

Those surfaces keep natural date spacing or their native coordinate and must not show
`Trading Days` labels. A true exception is recorded in §7 and in the owning feature
authority.

## 2. Modes

### Trading Days (default)

- Ordered trading-session domain supplied by the result; every session occupies one
  equally spaced position.
- Weekends/holidays occupy no space.
- Positions for sessions without a value are retained; a missing series point never
  changes the shared axis.
- All series and event annotations share one date→position mapping.
- A mark or event outside the domain is a contract error: fail explicitly, never shift
  or silently drop it.

### Calendar Days

- The original canonical `YYYY-MM-DD` values on real date spacing.
- Non-session intervals keep their horizontal span; no interpolation, no synthesized
  dates and no filled values.

Both modes display exactly the supplied dates and values; only the x presentation
changes.

## 3. Domain ownership and data boundary

The authoritative domain is producer-owned payload data. W1 uses the report's
`candidate_dates`; W2 uses `BacktestResult.daily[].trade_date` in result order. The
frontend consumes it unchanged and never derives sessions from contract codes, market
calendars, weekday heuristics, provider calls or another feature.

The domain is ordered, strictly increasing and covers every mark and event of the charts
it controls. That coverage is guaranteed by the owning result contract (W1 candidate
dates, W2 [RESULT](../market_backtesting/cases/futures_roll_long/RESULT.md) daily
series); the frontend never repairs, trims, sorts or extends it. An out-of-domain
reference fails explicitly at projection time.

Mode is frontend presentation state only:

```text
not changed by a mode switch
--------------------------------
producer View and its coordinates
raw dates and numeric values
statistics / PnL / return / drawdown
evidence / fingerprint
HTTP request, preflight, run identity or run request
```

Switching modes performs no HTTP request and no backend recomputation, and is never
written to the Run Request, URL, `localStorage` or `sessionStorage`. No Visualization V2
schema change is involved: `ordinalDates` remains a frontend renderer option.

The generic renderer keeps natural date spacing as its default. `Trading Days` is a
research-surface default supplied by the feature, never a `ChartView` default.

## 4. UI standard

- Ant Design `Segmented` with exactly `Trading Days` and `Calendar Days`.
- Default `Trading Days`.
- One controller controls every related chart of the same result; a chart group never
  has two independent switches.
- Implemented once as the shared
  [`DateAxisControl`](src/shared/visualization/DateAxisControl.tsx). Features supply the
  accessible label, place the control and hold the mode state; placement is
  feature-owned.
- Switching only changes presentation state; no confirmation, reload or request.

## 5. Interaction invariants

Both modes retain Zoom, Pan, Reset, hover tooltip with the real date and supplied
value/details, legend visibility, event annotations, missing-value presentation and the
original y-axis formatting and units.

On a mode switch:

- reset the horizontal viewport to the full range of the new coordinate system;
- never reuse an x range expressed in the other coordinate system;
- keep user legend selection, marks, events, values and units;
- prevent Plotly from resetting to a stale first coordinate system.

Trading Days tick density is bounded by the generic renderer, and axis/hover aliases
keep the real dates. Zoom/pan changes only the viewport.

## 6. Acceptance

Feature-local unit/component checks: default mode; switch; synchronized charts; repeated
switching; trading x = ordinal positions; calendar x = original dates; identical y data;
event/entry/roll/exit mapping; no result mutation; no HTTP/run request; default restored
for a different Run.

Chromium acceptance: both modes' actual axis type and trace coordinates; synchronized
charts; measurable spacing difference across a long non-session interval; Zoom, Pan and
Reset in both modes; legend retention; tooltip real date; event alignment; no new request
and no value change.

Evidence lives in the owning feature acceptance record.

## 7. Conformance inventory

| Surface | Domain source | Status |
| --- | --- | --- |
| W1 historical basis charts (`basis_value`, `basis_ratio`, `annualized_basis_ratio`) | report `candidate_dates` | conforming; one shared control in `Report` |
| W2 cumulative return and drawdown | `BacktestResult.daily[].trade_date` | conforming after UI-WP01; one control in `Result` |
| Research Explorer published-View reader | none for arbitrary publications | exception: no authoritative session domain; keeps natural date spacing, no mode control |
| W1 histogram charts, W2 trades/rolls tables | category / numeric / tabular | not applicable: no date x-axis |
| MO Option Chain, MO Premium Plane | strike / numeric plane | not applicable: no date x-axis |

Repository-wide review of current date-axis charts: the W1 reader (also used by the
offline report and static demo) and the W2 result are conforming; the Research Explorer
exception is recorded because inventing a trading calendar there would violate §1. No
other current analytical chart uses a date x-axis.
