# W2 current authority reconciliation

This document specializes the [case](ARCHITECTURE.md). It owns the current
Concern → Authority → Code Consumer inventory, semantic review, implementation drift
register and reconciliation verification. It defines no alternative financial or
execution contract. Follow the linked canonical owner for each requirement;
[Roadmap](ROADMAP.md) owns delivery sequence and readiness. This is a current-state
audit, not an archive of previous designs or implementation stages.

## Authority and consumer inventory

Paths in the consumer column are relative to `market_backtesting/src/market_backtesting/`
unless prefixed with a repository module; test paths are repository-relative. Pending
consumers have no runtime/API yet.

| Concern | Canonical authority | Current / planned code consumer |
| --- | --- | --- |
| Repository module identity, Python runtime and top-level dependencies | [Root architecture](../../../ARCHITECTURE.md) | Root package configuration; architecture checks |
| Module boundary, Core/case dependency direction and navigation | [Module architecture](../../ARCHITECTURE.md) | `core/`, `cases/futures_roll_long/`, package root; `market_backtesting/tests/test_architecture.py` |
| Core identity and bounded single-instrument scope | [Core architecture](../../core/ARCHITECTURE.md) | `core/__init__.py`; pure Core import tests |
| Time advancement, Policy invocation, failure propagation, Recorder | [Core Replay](../../core/REPLAY.md) | `core/replay.py::replay`; `core/models.py::ReplaySession`, `DailyRecord`, `ReplayResult` |
| Actual/Target Portfolio, market quote selection, unique Daily PnL, reference updates, StateEvents | [Portfolio Transition](../../core/PORTFOLIO_TRANSITION.md) | `core/transition.py::transition_portfolio`; `core/models.py::Portfolio`, `TargetPortfolio`, `TransitionResult` |
| Explicit InitialCapital, Daily Return, cumulative PnL/Equity/Return | [Core Accounting](../../core/ACCOUNTING.md) | `core/accounting.py::account`; `core/models.py::AccountingState`; D1 closed below |
| W2 identity, request constraints and first real research | [Case architecture](ARCHITECTURE.md) | `application_models.py::FuturesRollRequest`, `validate_futures_roll_request`; `application.py::FuturesRollService` |
| One-lot M1 entry, expiry M1/Q1 targets, final close, real contract versus Slot | [Strategy](STRATEGY.md) | `cases/futures_roll_long/policy.py::MechanicalRollPolicy`; `cases/futures_roll_long/models.py::DecisionContext` |
| Public market facts, completeness, date-indexed facts, W1 import grant, causality assumptions | [Inputs](INPUTS.md) | Synthetic `cases/futures_roll_long/replay.py::replay_futures_roll`, `cases/futures_roll_long/validation.py`; retained `IndexClose` series; `input_validation.py`, `public_inputs.py`, `fingerprint.py`, `preflight.py` |
| W1 pure Slot semantics | [W1 Slot Resolution](../../../market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md) | `cases/futures_roll_long/policy.py::_resolve` via the public facade only |
| Calendar / Futures / Index public facts and operations | [Calendar Service](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md), [Futures Service](../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md), [Index Service](../../../data_lake/datasets/tushare_index_daily/SERVICE.md) | `application.py::prepare` through the three published factories; retained final exports and separate SSE Calendar prerequisite |
| W2 InitialCapital derivation, multiplier consistency, Benchmark/Excess/Drawdown, case oracles | [Performance](PERFORMANCE.md) | Synthetic capital/equity checks in `cases/futures_roll_long/replay.py`, multiplier checks in `cases/futures_roll_long/policy.py`; `cases/futures_roll_long/performance.py::analyze_futures_roll`; both five-day oracles accepted |
| BacktestResult, trades/roll projections, full evidence/replay, limitations and V2 views | [Result](RESULT.md) | `result_models.py`, `result.py`, `result_validation.py`, `visualization.py`; full portable format under [Evidence](EVIDENCE.md), `evidence_models.py` and `evidence.py` |
| Independent online request/run/store, owner isolation and failure composition | [Online Application](ONLINE_APPLICATION.md) | Pending WP5; consumes Core + Analyzer + Result |
| HTTP/OpenAPI and Web presentation | [HTTP architecture](../../../ui_http/ARCHITECTURE.md), [HTTP catalog](../../../ui_http/HTTP_PRODUCTS.md), [Web workspace](../../../ui_web/workspace.md) | Pending WP6/WP7; no W2 endpoint, DTO or active feature claimed |
| Current completion, remaining WPs and acceptance boundaries | [Roadmap](ROADMAP.md) | Subsequent implementation tasks; no business runtime consumer |
| Execution policy and task navigation | [Root AGENTS](../../../AGENTS.md), [Module AGENTS](../../AGENTS.md) | Agents working in this module |

The module/Core/case entries select the next contract; formulas and detailed state,
input, result and run semantics stay in their narrowest owners. Recorder is the
in-memory construction of immutable daily records, not a new runtime framework.
Analyzer consumes accounting; it never replays transitions or creates a ledger.

## Authority change matrix

| File | Change | Reason |
| --- | --- | --- |
| [Root AGENTS](../../../AGENTS.md) | Route current state through module authority | Keep agent entry current without an implementation history |
| [Root architecture](../../../ARCHITECTURE.md) | Current package/runtime identity; remove transitional status | Root owns stable boundaries, not delivery process |
| [Module AGENTS](../../AGENTS.md) | Add current audit navigation and verification rules | Make drift and documentation checks discoverable |
| [Module architecture](../../ARCHITECTURE.md) | Separate Core/case concerns; delegate status and audit | Avoid duplicated strategy details and stale readiness |
| [Core architecture](../../core/ARCHITECTURE.md) | Navigate daily and cumulative accounting | Make Daily Return ownership explicit |
| [Core Replay](../../core/REPLAY.md) | Ordered daily flow and snapshot handoff | One clock and no second market-data selection service |
| [Portfolio Transition](../../core/PORTFOLIO_TRANSITION.md) | Real-ID quote selection; complete events versus trades | Preserve PnL attribution and exact state reconstruction |
| [Core Accounting](../../core/ACCOUNTING.md) | Canonical daily-return output/formula and fixed capital | Core owns all strategy accounting |
| [Case architecture](ARCHITECTURE.md) | First IM research scope, current navigation/status delegation | Fix the acceptance target without request defaults |
| [Strategy](STRATEGY.md) | Current Policy/Core test and failure handoff terminology | No separate holding executor |
| [Inputs](INPUTS.md) | Validated date-queryable facts and adapter/replay/transition split | Maintain price-free Policy and public upstream boundaries |
| [Performance](PERFORMANCE.md) | Consume Core returns; own cumulative excess definition | Eliminate Case-side daily-return computation |
| [Result](RESULT.md) | Projection equality, full event evidence and explicit limitations | Consume canonical values without duplicate formulas |
| [Online Application](ONLINE_APPLICATION.md) | Core/Analyzer composition and current failure vocabulary | Align planned execution with existing public failures |
| [Roadmap](ROADMAP.md) | Single current delivery view and Remaining WP2–WP8 gates | Remove completed-work instructions and duplicated history |
| This reconciliation | Current inventory, review, D1 and validation evidence | Separate implementation differences from semantic contracts |

## Current semantic review

Classifications are **Compatible**, **Requires Authority Change**, **Deferred**, or
**Blocking**. Requires Authority Change identifies a concern resolved by this
consolidation, not an outstanding competing authority. Unimplemented authorized
capabilities are Deferred delivery; a mandatory mismatch in existing code is Drift.

| # | Concern | Classification | Current resolution / evidence |
| --- | --- | --- | --- |
| 1 | Core contamination by W2 | Compatible | Core owns generic single-real-instrument replay; one lot, products and Slots belong to Policy. Architecture tests block case/upstream imports from Core and package root. |
| 2 | Unique Daily PnL owner | Compatible | Transition is the sole owner; independent PnL reconstruction and roll-gap oracle check actual incoming instrument attribution. Accounting/Analyzer consume it. |
| 3 | Daily Return ownership | Requires Authority Change | Core Accounting exclusively defines and exposes it; Case projects it. D1 is closed by immutable Core daily return and unchanged Analyzer projection. |
| 4 | Market snapshot selection | Requires Authority Change | Adapter prepares validated read-only facts, Replay hands off session inputs, Transition selects required real-instrument quotes. No second selector, Accounting lookup or post-roll Slot-based PnL identity. |
| 5 | Event reconstruction | Compatible | Full ordered StateEvents reconstruct reference/date as well as instrument/quantity; `position_changes` is the trade subset. Existing event reconstruction test covers hold and roll. |
| 6 | Case repeats Core accounting | Requires Authority Change | Performance references Core daily/cumulative outputs; Result checks projection equality. Financial formulas have one canonical owner; worked oracles are verification examples. |
| 7 | W1 Slot transitions versus W2 rolls | Compatible | Policy resolves Slots on entry/expiry decisions only. A role change alone is no trade; authorized facade symbols and architecture tests preserve isolation. |
| 8 | Look-ahead risk | Compatible | Price-free current context, configuration-only Policy and current/future Close perturbation tests enforce price isolation. Metadata/active-set point-in-time availability is an explicit assumption, not a historical freshness proof. |
| 9 | Result / Online execution model | Requires Authority Change | Result consumes Core evidence plus Analyzer; Online composes the same path. Failure stage/category vocabulary follows Policy/Core/case ownership. No separate holding executor or ledger. WP4 Result is implemented; Online remains WP5. |
| 10 | Completed work versus future Roadmap | Requires Authority Change | Package, Core and W2 synthetic adapter are present. WP2–WP4 are accepted and WP5–WP8 remain pending; no package/simulator recreation or dual roadmap. |
| 11 | Duplicate / contradictory authority | Requires Authority Change | Entries navigate; specialized contracts own formulas and workflows. Current audit is separate from Roadmap. No previous-version authority or compatibility chain is maintained. |
| 12 | Residual implementation mismatch | Requires Authority Change | D1 is closed with independent daily-return tests and both Performance oracles. Missing later-WP deliverables are not mislabeled as regressions. |

No Blocking semantic decision is identified. DataLake integration and bounded real
IM input acceptance are complete in WP3. Formal Result/Evidence/Views and retained-real
reproduction are complete in WP4. Online, HTTP/Web and full-window real E2E acceptance
remain **Deferred** to WP5–WP8, not evidence of completed W2.
Existing DataLake/W1 contracts and HTTP/Web planned boundaries suffice; this reconciliation changes no producer contract or sibling code.

## Implementation drift register

### D1 — Core daily-return output (CLOSED)

| Field | Current finding |
| --- | --- |
| Authority Requirement | [Core Accounting](../../core/ACCOUNTING.md) owns daily return, cumulative PnL, Equity and cumulative return. Case consumes them unchanged. |
| Status | **CLOSED — 2026-11-11, Remaining WP2 acceptance PASS.** |
| Actual Code Behavior | Frozen `AccountingState.daily_return` starts at zero. `account()` computes and finite-validates it using fixed InitialCapital. Analyzer projects it unchanged. |
| Affected File / Symbol | [core/models.py](../../src/market_backtesting/core/models.py): `AccountingState`; [core/accounting.py](../../src/market_backtesting/core/accounting.py): `account`; [performance.py](../../src/market_backtesting/cases/futures_roll_long/performance.py): `analyze_futures_roll` |
| Acceptance / Test Evidence | `test_core_accounting.py`: initial/flat/entry, positive/negative/zero/roll, fixed capital, immutability, invalid values, cumulative/equity/daily-return overflow and simple-return sum. `test_futures_roll_performance.py`: unchanged Core projections, finite/positive equity and both independent five-day oracles. |
| Remaining Action | None for D1. No other open Implementation Drift is identified in the implemented synthetic subset. |

### D2 — Definition version confused with case identity (CLOSED)

`PreparedFuturesRollInputs.definition_version` now uses the canonical
`futures_roll_long_definition_v1`. Case, definition, result and input identities are
explicitly tested as four distinct values; no compatibility adapter exists.

No open mandatory mismatch is identified in the implemented Core/W2/WP4 subset.
The Index SSE Calendar prerequisite discovered in fresh-cache real acceptance is
explicitly reconciled in [Inputs](INPUTS.md#reconciled-index-calendar-prerequisite)
and implemented through the Calendar public service, without producer changes.
The register does not weaken full StateEvent reconstruction, causal price isolation,
real-instrument attribution or fail-without-partial-success requirements.

## Deferred and blocking decisions

- **Blocking: none.** D1/D2 are closed; WP2–WP4 are accepted; WP5 may start.
- **Deferred delivery:** Online mapping/store (WP5),
  HTTP/OpenAPI (WP6), Web (WP7), real IM and Windows Chrome → WSL acceptance (WP8).
- Historical metadata availability stays an explicit research limitation. Proving
  point-in-time availability or provider-current freshness is not implied by replay.
- Excluded features and platform/deployment limitations remain in
  [Roadmap](ROADMAP.md#deferred-and-known-limitations); no framework is prebuilt for them.

## Validation evidence

Actual WP3 validation on 2026-11-11, using the repository-root Poetry
environment. Synthetic fixtures use the real W1 Slot resolver and MechanicalRollPolicy;
they do not claim real Calendar completeness or real-market acceptance.

| Command / review | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests` | PASS — 319 tests, including all 213 prior tests, public-service failure matrix, SSE prerequisite, canonical fingerprint, read-only preflight and both financial oracles |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py` | PASS — 21 tests |
| `poetry run ruff check market_backtesting` | PASS |
| `poetry run mypy market_backtesting` | PASS — 32 source files |
| `poetry run pytest data_lake/tests/test_boundary.py market_research/tests/test_boundaries.py` | PASS — 15 tests |
| `git diff --check` | PASS |
| Read-only Markdown link/anchor and navigation audit | PASS — 127 local links/anchors; Root → module → case → Inputs navigation checked |
| Full diff and ownership review | PASS — Core owns strategy accounting; case owns benchmark/risk; changes confined to `market_backtesting`, with no W1/DataLake producer, Core or Policy changes |

All 213 prior Core/Policy/Performance tests remain in the passing suite. No test was
skipped and no financial oracle or isolation assertion was removed.

### Actual five-day oracle results

The independent expected tables are in [Performance](PERFORMANCE.md#manual-independent-oracle).
The synthetic entry active months are 202601/202602/202603/202606; expiry active
months are 202602/202603/202606/202609. The February contract enters as M1 and
expires as M0; the actual resolver selects March M1 or June Q1. No resolver is mocked.

| Measure | M1 actual | Q1 actual |
| --- | ---: | ---: |
| Initial notional (CNY) | 1,200,000 | 1,200,000 |
| Daily PnL (CNY) | 0 / 10,000 / 10,000 / 4,000 / -2,000 | 0 / 10,000 / 10,000 / 1,000 / -2,000 |
| Total PnL (CNY) | 22,000 | 19,000 |
| Gross return | 0.018333333333333333 | 0.015833333333333335 |
| Benchmark return | 0.012499999999999956 | 0.012499999999999956 |
| Excess return | 0.005833333333333378 | 0.003333333333333379 |
| Strategy maximum drawdown | -0.0016339869281045694 | -0.0016380016380016515 |
| Benchmark maximum drawdown | -0.004950495049505177 | -0.004950495049505177 |

Return/drawdown comparisons use absolute tolerance 1e-15; benchmark equity uses
absolute tolerance 1e-9 CNY, with no intermediate rounding. Tests verify roll gap
exclusion, replacement reference prices, final-session PnL and flat termination,
separate running peaks and holding-period excess rather than summed daily excess.

## WP3 fake-service failure matrix

Tests use real published Export/Row/Coverage/Ensure types and documented immutable
scope/window shapes, with the actual W1 resolver and MechanicalRollPolicy.
`test_public_inputs.py` and `test_readiness.py` cover every requested matrix entry:

| Requested cases | Actual coverage |
| --- | --- |
| 1, 22 — complete inputs, M1/Q1 real-ID roll attribution | Five-session public-service executions: 22,000 / 19,000 CNY; old-contract roll PnL; replacement Close reference; terminal Flat |
| 2–3 — missing Calendar, scope/schema | Missing/duplicate dates, wrong exchange/window/schema, bool flags/counters, inconsistent coverage |
| 4–7 — Futures completeness/duplicates/metadata/delist | Final incomplete export; duplicate contract/date; identity/month/product conflicts; invalid/non-session expiry |
| 8–10 — entry/roll/Slot/Close | Missing decision/held rows, irregular active set, missing/non-finite/non-positive Close; no ensure for malformed facts |
| 11–14 — Index | Incomplete proof; wrong underlying/scope/row identity; missing CFFEX Close; duplicate/date/numeric failures; SSE-only rows retained but not replayed |
| 15–17 — operation/ensure/final export | Both public error types; ensure OperationError; malformed EnsureResult; incomplete ensure retained; final complete succeeds, final incomplete/malformed fails |
| 18–19 — fingerprint | Golden synthetic digest; full public field enumeration; ISO/float64 hex/Unicode; signed-zero and fact/proof changes; profile-independent input identity |
| 20–21 — read-only/no credential | Read-only services without ensure; poisoned preparation/replay/analyzer; missing real public caches for each dependency; Source initialization forbidden, no cache directory created |
| 23 — no successful partial result | Every failure raises typed error without replay/fingerprint success; pure category/reason/date/contract preserved |
| Additional prerequisite/boundary checks | SSE exact-window export/ensure/export; malformed SSE fails without ensure; at most one ensure; no redundant coverage; request/span validation before I/O; frozen retained inputs; authorized symbols only |

## WP3 bounded real IM acceptance

**PASS — 2026-11-11**, public production factories and API, fresh isolated temporary
Dataset storage, real Tushare data. The first attempt exposed the missing independent
SSE Calendar prerequisite; that contract gap is closed in Inputs and the successful
fresh-cache acceptance includes it. No default cache was read, changed or rebuilt.

| Proof | Actual result |
| --- | --- |
| Requested / observed window | 2025-02-17 through 2025-03-24, inclusive |
| CFFEX Calendar / auxiliary SSE Calendar | 36/36 natural-day units each, complete, zero missing/pending/failed |
| Futures / Index coverage | 26/26 product-day / index-day units, complete, zero missing/pending/failed |
| Futures rows / replay sessions | 104 real contract rows / 26 actual CFFEX sessions |
| Actual held expiry / old Close | IM2503.CFX, Source delist_date 2025-03-21, Close 6414.2 |
| M1 replacement / roll Close | IM2504.CFX / 6318.2 |
| Q1 replacement / roll Close | IM2506.CFX / 6177.4 |
| Fixed initial notional | 1,256,313.1600000001 CNY |
| M1 total PnL / gross return | 31,360.00000000003 CNY / 0.024961929078256274 |
| Q1 total PnL / gross return | 32,080.000000000102 CNY / 0.025535034592808134 |
| Benchmark return, both profiles | 0.012540726708617722 |
| Roll attribution / replacement reference / final Flat | PASS for both profiles |
| Retained-input replay and Analyzer / repeated cached execution | PASS, identical replay/performance/fingerprint |

Real canonical fingerprint (both profiles):
`0ff0446fa3f534139dc1c1d4ed3c1667fce68821e9670aa9a7116f96c9022e7b`.
Synthetic golden fingerprint:
`5edcf4bad7ff0232471cda6d83bfbf423ac27ad659bd04659863d9621377b480`.
The profile is `futures_roll_long_inputs_v1`; credentials, local paths and ensure
outcomes do not enter canonical bytes. Full final public facts were retained locally
as canonical JSON along with the acceptance summary at
`/tmp/w2-wp3-real-im-24g0cxfw/` (disposable local evidence); API results also retain typed
exports and the separate SSE prerequisite. This is not a WP4 Evidence Package.

Reproduce bounded real acceptance from the root with
`poetry run python market_backtesting/tests/real_market_acceptance.py`.
This explicit opt-in script prints its temporary artifact location, uses test-only
storage redirection permitted by DEVELOPMENT.md, and never runs in pytest. Missing
credential/Source/network yields a truthful NOT RUN report. Synthetic tests remain
independent of that environment.

## WP4 verification — 2026-11-11

**WP4 PASS.** Formal BacktestResult, complete portable evidence and offline
reproduction are implemented within the case; Core/Policy/Analyzer remain the single
execution and financial owners. Ordinary projection never reruns Replay/Analyzer.
`prepare`, `run` and `preflight` retain their WP3 behavior.

[Result](RESULT.md) owns the immutable payload and cross-field checks;
[Evidence](EVIDENCE.md) owns the separately consumable portable format/API. The only
financial-contract clarification is that Σ Daily PnL uses Core's chronological
binary64 addition order. Python 3.13's compensated `sum()` differs on real retained
inputs; validation now compares the authoritative ordered sum without rounding or
tolerance. A fixed independent binary64 sentinel test covers the distinction.

| Verification category | Actual outcome |
| --- | --- |
| Synthetic Oracle | **PASS** — M1 22,000 CNY, Q1 19,000 CNY; exact daily Core projections, unchanged Analyzer outputs, entry/hold/roll/final attribution |
| Fake-Service Integration | **PASS** — public WP3 preparation to validated Result/Evidence, request versus observed dates, final-expiry close-only, event order, immutable safe output |
| Offline Evidence Reproduction | **PASS** — both profiles, canonical fingerprint, complete ordered marks/close/open, portfolios, pricing/accounting/performance/result equality, missing/reordered/tampered/invalid evidence rejection |
| Visualization V2 | **PASS** — producer validation plus unchanged frontend `validateViewV2`; four dynamically generated synthetic views and four retained-real views, eight Vitest assertions per fixture set |
| Actual Real-Market Acceptance (bounded WP4) | **PASS** — retained real IM inputs, 2025-02-17 through 2025-03-24, both profiles, no Source acquisition |
| Online/HTTP/Web and full-window WP8 | **NOT RUN** — deferred WP5–WP8 |

Bounded IM verification uses the WP3 retained canonical JSON and public SSE Calendar
export from its isolated acceptance cache, not direct SQLite access. Both runs retain
26 sessions, 4 executions, 1 roll, 29 complete StateEvents and final Flat. Actual
M1/Q1 PnL is 31,360.00000000003 / 32,080.000000000102 CNY; gross return is
0.024961929078256274 / 0.025535034592808134; benchmark return remains
0.012540726708617722. Real contract IDs and the three-export fingerprint remain
unchanged: `0ff0446fa3f534139dc1c1d4ed3c1667fce68821e9670aa9a7116f96c9022e7b`.
SSE is retained independently and remains outside that fingerprint.

Portable packages, formal results, generated views, frontend conformance output and
acceptance report are retained outside Git at `/tmp/w2-wp4-real-im-61h8srkx/`.
This disposable verification location is not an API dependency or online store.
Repeat against any retained WP3 root with:

```bash
poetry run python market_backtesting/tests/real_result_acceptance.py --retained-root PATH
```

Missing retained inputs report NOT RUN; inconsistent evidence fails. The script
never invokes Source acquisition. Tests preserve all 319 previous regressions and
add independent Result/Evidence/V2 acceptance.

| Final required check | Outcome |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | **430 passed**, including 319 prior regressions and the isolated frontend validator subprocess |
| Snapshot authority topology / HTTP architecture / DataLake boundary / Research boundaries | **36 passed** |
| `poetry run ruff check market_backtesting` | **PASS** |
| `poetry run mypy market_backtesting` | **PASS**, 41 source files |
| `git diff --check` | **PASS** |

No architecture guard was weakened; decoder imports fit the existing authorized
public-symbol whitelist. No sibling production code or frontend schema changed.

Reconciliation Summary: **WP4 PASS**. No open Implementation Drift or blocking
semantic decision. **WP5 may start**; this delivery stops before WP5. W2 remains
incomplete pending Online/HTTP/Web and full-window WP8 acceptance.
