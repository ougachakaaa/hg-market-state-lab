# Futures Roll Long public inputs, completeness and reproduction

This contract specializes the [case](ARCHITECTURE.md) and the repository's public
upstream boundaries. Only input preparation acquires market facts. Policy, Core Replay and result projection consume retained validated inputs and perform no
market I/O.

## DataLake-first selection

The case uses DataLake public Application Services directly. No Snapshot Product is
selected as a fallback, and no second market cache, provider client, SQLite reader or
Research Observation/Report is an input.

| Required facts | Exact public boundary |
| --- | --- |
| CFFEX sessions | `data_lake.datasets.tushare_trade_calendar`: `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`, view `calendar`, export schema 1 |
| Futures Close, real identity, multiplier, delivery month, lifecycle and underlying | `data_lake.datasets.tushare_equity_index_futures`: `FuturesDailyRange(product_codes=[product_code], start_date, end_date)`, view `futures_daily`, export schema 2 |
| Benchmark index Close and name | `data_lake.datasets.tushare_index_daily`: `IndexDailyRange(index_codes=[underlying_index_code], start_date, end_date)`, view `index_daily`, export schema 1 |

Use each module's published `create_service()` and semantic `coverage` / `ensure` /
`export` operations under [Calendar](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md),
[Futures](../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md) and
[Index](../../../data_lake/datasets/tushare_index_daily/SERVICE.md) contracts. The
underlying relationship is read from the Futures public rows and remains owned by
[Futures facts](../../../data_lake/datasets/tushare_equity_index_futures/FACTS.md);
W2 must not maintain a second product-to-index mapping.

A legal public Export may be incomplete. W2's policy is stricter than a descriptive
observation: every required input must be complete for the requested window before a
backtest may start. There is no partial-input BacktestResult in v1.

## Preparation sequence

1. Validate the semantic request without I/O: product, date-only inclusive window,
   profile, date order, Asia/Shanghai future limit and maximum span.
2. Acquire the exact-window CFFEX Calendar export. If incomplete, call its public
   `ensure` once for the same request, retain the outcome, then export again. Validate
   the final envelope and completeness. Do not call `coverage` redundantly.
3. Acquire the one-product Futures export in the same pattern. Validate its final
   envelope and every required public row/metadata association.
4. Derive the benchmark `underlying_index_code` from the validated Futures rows. All
   retained rows for the product must agree. If no row exists or more than one distinct
   underlying is present, fail input preparation.
5. Acquire the mapped Index export in the same pattern. Validate the final envelope and
   completeness for the whole window.
6. Build read-only, date-queryable market facts: ordered CFFEX sessions, per-session
   active contract evidence, metadata/instrument references, Futures Close snapshots
   and Index Close facts. All required facts are retained as one semantic input identity.
7. Compute the canonical input fingerprint. The adapter builds price-free decision
   contexts and `ReplaySession.snapshot` inputs from these retained facts. Policy calls
   the authorized Slot resolver only for entry/roll decisions. Begin pure Core Replay;
   no further market I/O occurs after preparation.

Input Adapter owns validation and preparation of the market-fact set. Replay owns
clock advancement, Policy invocation and the handoff of each retained snapshot.
[Transition](../../core/PORTFOLIO_TRANSITION.md) determines necessary valuation and
execution quotes by Previous/Target real instrument IDs inside that snapshot. Neither
Accounting nor Analyzer queries a market service or reselects a PnL instrument by Slot.
No additional market-data framework or selection owner is required.

`ensure` is not a repair mechanism for a malformed export. A malformed envelope,
counter set, scope/window, row identity or public fact fails immediately; it is never
passed to `ensure` to be "fixed". A recoverable `EnsureResult.failure` is retained as
diagnostic evidence, but only the final complete Export is the input proof.

## Completeness and shape validation

For each final export, validate together:

- exact `dataset`, `view` and `export_schema_version`;
- exact scope/window matching the semantic request;
- non-bool integer counters, mutual accounting and the complete-count formula;
- `complete == true` with zero missing/pending/failed units;
- payload rows belonging only to the requested scope/window;
- ordered, unique public identities;
- all required public fields and types, including metadata/lifecycle consistency;
- proof and payload from the same export, not a mix of calls or cache snapshots.

Calendar:

- one record for every natural date in the inclusive window;
- `is_open` is integer 0 or 1; `pretrade_date` is a valid date or null;
- the open dates are strictly increasing and define the study sessions;
- fewer than two open sessions fails `insufficient_sessions`.

Futures:

- coverage targets one product × every CFFEX open session in the window;
- each successful product-day's rows represent its complete active ordinary contract
  set, as proven by the DataLake export contract;
- within one product-day, `(contract_code, trade_date)` is unique and rows agree on
  product, underlying, delivery month, multiplier and lifecycle;
- across sessions, the same `contract_code` has consistent metadata; a conflict fails;
- a successful zero-row product-day is not silently treated as an empty market when a
  strategy decision needs a contract; entry/roll/holding requirements fail explicitly;
- the export's scope/window and coverage must match the Calendar-derived target exactly.

Index:

- coverage is complete for the mapped index over the requested window;
- there is exactly one row for each CFFEX open session used by the strategy, with
  canonical `index_code` matching the derived underlying and a finite `Close > 0`;
- extra SSE-only rows do not create strategy sessions, but their presence does not
  excuse a missing CFFEX-session Close;
- the index display name, if used, comes from the public rows and must be consistent.

W2 does not reconstruct DataLake's expected contract universe, fetch a catalog or
re-read Dataset persistence. The published complete export is the active-set proof.
W2 must not treat arbitrary quote availability, volume, open interest or a missing row
as proof of an empty active set.

## Authorized W1 Slot resolution reuse

W2 reuses the existing public pure Slot resolution boundary of the W1 Futures Basis
case rather than implementing a second algorithm. The semantic owner remains
[W1 Slot resolution](../../../market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md);
W2 does not change its formulas, carriers, code or behavior.

The only permitted import symbols from
`market_research.descriptive.cases.futures_basis` are:

```text
resolve_daily_slots
ContractMetadata
DailyUniverseEvidence
DailySlotResolution
SlotMapping
SlotResolutionError
SLOTS
```

The following use is required:

- call `resolve_daily_slots` only on entry and roll decision sessions;
- construct `ContractMetadata` from the validated final Futures rows' public fields;
- construct `DailyUniverseEvidence` with `complete=True`, the exact unique active
  contract codes and a nonempty `source_export_ref` tied to the retained final export;
- treat its ordered `M0 / M1 / Q1 / Q2` mappings as the decision-day roles;
- map a `SlotResolutionError` or an `not_applicable` target to a strategy input
  failure; never repair, substitute or infer a target.

The following are not authorized and must not be imported or called: transition
detection, Observations, observation construction, Sample Conversion, Statistics
adaptation, Report, Evidence, Publication, Preflight, or the W1 online application.
A W1 Slot transition is a descriptive mapping change, not an execution; W2 must not
turn it into a roll.

This is a symbol-level consumer grant in the repository and module authority, not a
general permission to consume Research. If the W1 public facade cannot provide the
required isolation, stop and report the boundary conflict; do not copy the Slot
algorithm into W2. Current isolation is checked by the Backtesting architecture tests;
WP3 must preserve that boundary.

## The synthetic `DailyUniverseEvidence` contract

W2 does not create a new completeness proof. The evidence carrier is a handoff over
already validated public facts. Its `source_export_ref` is a stable W2-owned reference
derived from the final Futures export identity (for example, dataset/view/schema,
product, date and input fingerprint). It is not a filesystem path, credential,
provider response or claim that a boolean authenticates completeness. The full final
export is retained by WP3/WP4 evidence, so the reference can be audited.

The W2 active-contract set is the set of real rows that DataLake proved complete for
that product-day. W2 must not union metadata across dates, borrow adjacent-day
metadata, use a current catalog to reconstruct a past day or infer a replacement.

## Canonical input identity and fingerprint

The case-owned profile is `futures_roll_long_inputs_v1`. Its canonical payload is:

```text
{
  "profile": "futures_roll_long_inputs_v1",
  "calendar_cffex": <final TradeCalendarExport public fields>,
  "futures": <final FuturesDailyExport public fields>,
  "index": <final IndexDailyExport public fields>
}
```

Encode it deterministically using only public semantic field names:

- dates as ISO `YYYY-MM-DD`;
- finite binary64 float fields as `["float64", value.hex()]`, retaining signed zero
  and avoiding display rounding;
- public integers, booleans, strings and nulls as JSON integer, boolean, string and
  null;
- ordered public sequences as arrays in their validated producer order;
- UTF-8 JSON, `sort_keys=true`, `ensure_ascii=true`, compact separators, no BOM, no
  trailing newline and no NaN/Infinity;
- SHA-256 lowercase hexadecimal of those bytes.

This is a case-specific encoding, not a generic serializer framework. It does not
reuse or reinterpret the W1 `futures_basis_inputs_v1` profile. Request identity and
actual input identity are separate; changing a final fact or proof changes the
fingerprint under the same request.

The result's evidence section records the profile, fingerprint, exact public requests,
coverage, source identities and definition version. WP4 owns the fuller evidence
package and replay verification; its canonical bytes must reproduce the same
fingerprint. A fingerprint alone is not a substitute for retained inputs.

## Read-only readiness assessment (preflight)

Preflight is an application-level, read-only assessment for the Web admission step. It
never calls `ensure`, performs Source I/O, creates a run or writes a cache.

It evaluates, where the public read-only facts permit:

| Dependency | Assessment |
| --- | --- |
| `calendar_cffex` | request validity + Calendar coverage/export for the exact window |
| `futures` | product target coverage for the exact window; underlying derivation when rows are available |
| `index` | mapped index coverage for the exact window when the underlying is known; otherwise `unknown` |

The response distinguishes `complete`, `incomplete`, `unavailable` and `unknown`.
`ready=true` means only that the exact public cache coverage is complete. It does not
validate row values, active-set structure, decision-day Slot resolution, future
provider freshness or the strategy's eventual success. Submission still performs the
full input preparation and validation; preflight is advisory and never a submission
gate or a successful-result promise.

If Calendar is incomplete, the target session set cannot be proven; downstream
readiness is `unknown` rather than guessed from weekdays or a partial date range. If
the underlying cannot be derived without a usable Futures row, Index readiness is
`unknown`. The limitation is reported to the user, not hidden.

## Failure semantics

The following fail input preparation and produce no successful result:

- invalid request; fewer than two CFFEX sessions; window beyond the maximum span;
- Calendar/Futures/Index operation failure, malformed envelope or illegal public row;
- incomplete Calendar/Futures/Index, wrong scope/window or mismatched target units;
- Futures active-set/metadata inconsistency, missing decision-day structure or
  ambiguous underlying;
- missing CFFEX-session Index Close, non-positive/invalid price or inconsistent
  index identity;
- W1 Slot resolution failure or a missing/illegal entry/roll target.

A failure may retain safe diagnostics and public evidence obtained so far. It must not
publish a successful input fingerprint, a partial BacktestResult, a filled price, a
guessed contract or a silently shortened window. No Snapshot fallback, second Source,
retry framework, date shift or alternate calendar is authorized.

## Decision context versus Close snapshot

W2 synthetic `FuturesRollInput` retains sessions, W1 metadata, session Close facts,
active-set evidence, explicit contract multiplier references and the underlying
index Close series. W1 ContractMetadata has no multiplier; W2 associates it separately and
never changes the W1 carrier. Multipliers are supplied, not guessed from product codes.
The adapter requires exact metadata-to-instrument identity associations; used contracts
must match the entry multiplier.

`FuturesRollInput.index_closes` is an immutable tuple of frozen
`IndexClose(trade_date, close)` rows. Its date sequence must equal the supplied CFFEX
sessions exactly, in order, with no missing, extra, duplicate or reordered row.
Dates are date-only; every Close is numeric (not bool), finite and strictly positive.
There is no separate initial-index-price input: the first row is the sole index
price used for N0, and the same series supplies the benchmark.
`FuturesRollReplay` retains this validated series and `benchmark_index_code`, derived
from the single underlying in validated contract metadata. Neither enters Policy or
DecisionContext. WP3's public Index adapter must map its validated CFFEX-session
rows into this same boundary; extra SSE-only dates are filtered during preparation,
not silently accepted by the synthetic boundary or Analyzer.

For each session the adapter exposes only current metadata/instrument references and
that date's evidence to Policy. Historical metadata are supplied as assumed known at
decision time; current export completeness does not prove a historically versioned
pre-close active set or metadata freshness. This limitation must remain explicit.
Current-session Close and future prices are exclusively Replay/Transition inputs;
Policy configuration retains no market input collection. Perturbing current/future
Close values must not change mechanical targets when price inputs remain legal.

The synthetic adapter computes the first price-free target once to obtain the entry
multiplier for capital derivation. Its callable returns that same immutable target to
Replay on the first session; subsequent decisions invoke MechanicalRollPolicy using
Replay's actual previous Portfolio. This does not perform an execution or introduce
a second clock; W1 Slot resolution still occurs once per entry/roll decision date.

## WP3 public Python application boundary

The canonical facade is `market_backtesting.cases.futures_roll_long`.
`FuturesRollRequest(product_code, start_date, end_date, strategy_profile)` is frozen,
has fixed `case="futures_roll_long_v1"`, and no business defaults.
`validate_futures_roll_request(request)` validates without I/O before any service
operation; application operations repeat validation (including the Shanghai today limit).

`create_futures_roll_service()` composes the three published Dataset factories.
Tests may inject the three public service dependencies by keyword (`calendar`,
`futures`, `index`); these are case-specific structural dependencies, not a generic
service framework. Neither factories nor read-only operations require credentials.

- `service.prepare(request) -> PreparedFuturesRollInputs` retains the exact public
  requests, three frozen final exports, ensure diagnostics, canonical fingerprint and
  existing `FuturesRollInput`. It does not resolve Slots or run the strategy.
- `service.run(request) -> FuturesRollExecution` prepares once, then calls the existing
  Replay and Analyzer once each. The frozen execution contains request, observed
  session bounds, replay, performance and prepared inputs. This is **not** the WP4
  `BacktestResult` or full Evidence Package; no run ID, persistence or transport is added.
- `service.preflight(request) -> FuturesRollReadiness` uses exports only. Each dependency
  has a state, safe reason and optional public coverage. Unknown dependencies are not
  queried. This operation does not invoke full row/Slot/strategy validation.

`FuturesRollApplicationError` specializes `FuturesRollError` with `stage`, optional
`dependency`, and retained safe ensure diagnostics. Input/acquisition failures use
case-owned categories/reasons; replay/analysis failures preserve the original
category/reason/date/contract. No error carries a successful partial execution or a
successful input fingerprint. Upstream exception text is not copied into diagnostics,
because public operation failures can contain runtime paths or provider details.

Legal incomplete exports must pass the same envelope, counters, public-field,
identity/order and payload accounting checks before ensure is permitted. Missing
Calendar records are legal only when accounted for by incomplete coverage; a complete
Calendar must contain every natural day. A complete Index export must have one row
per successful unit and a Close for every CFFEX session. Its own SSE target count is
producer-owned; W2 does not substitute the CFFEX count for it. Futures successful
zero-row units remain legal producer proofs, but cannot satisfy missing strategy facts.

Ensure results are retained as diagnostics, not fingerprint inputs. A returned
incomplete ensure is always followed by the final export; only that export determines
whether preparation can continue. All retained export sequences must be immutable
public tuples. The case-specific canonical encoder explicitly enumerates published
fields, rejecting illegal values rather than serializing internal object state.
