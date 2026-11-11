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
| Explicit InitialCapital, Daily Return, cumulative PnL/Equity/Return | [Core Accounting](../../core/ACCOUNTING.md) | `core/accounting.py::account`; `core/models.py::AccountingState`; D1 below |
| W2 identity, request constraints and first real research | [Case architecture](ARCHITECTURE.md) | Synthetic product/profile validation; public request/API pending WP3 |
| One-lot M1 entry, expiry M1/Q1 targets, final close, real contract versus Slot | [Strategy](STRATEGY.md) | `cases/futures_roll_long/policy.py::MechanicalRollPolicy`; `cases/futures_roll_long/models.py::DecisionContext` |
| Public market facts, completeness, date-indexed facts, W1 import grant, causality assumptions | [Inputs](INPUTS.md) | Synthetic `cases/futures_roll_long/replay.py::replay_futures_roll`, `cases/futures_roll_long/validation.py`; DataLake preparation/preflight pending WP3 |
| W1 pure Slot semantics | [W1 Slot Resolution](../../../market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md) | `cases/futures_roll_long/policy.py::_resolve` via the public facade only |
| Calendar / Futures / Index public facts and operations | [Calendar Service](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md), [Futures Service](../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md), [Index Service](../../../data_lake/datasets/tushare_index_daily/SERVICE.md) | W2 public Input Adapter pending WP3 |
| W2 InitialCapital derivation, multiplier consistency, Benchmark/Excess/Drawdown, case oracles | [Performance](PERFORMANCE.md) | Synthetic capital/equity checks in `cases/futures_roll_long/replay.py`, multiplier checks in `cases/futures_roll_long/policy.py`; full Analyzer pending WP2 |
| BacktestResult, trades/roll projections, full evidence/replay, limitations and V2 views | [Result](RESULT.md) | Existing synthetic `DailyProjection`/`Execution`/`RollEvent`; full result/evidence/projection pending WP4 |
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
| 3 | Daily Return ownership | Requires Authority Change | Core Accounting exclusively defines and exposes it; Case projects it. Existing implementation gap D1 remains open. |
| 4 | Market snapshot selection | Requires Authority Change | Adapter prepares validated read-only facts, Replay hands off session inputs, Transition selects required real-instrument quotes. No second selector, Accounting lookup or post-roll Slot-based PnL identity. |
| 5 | Event reconstruction | Compatible | Full ordered StateEvents reconstruct reference/date as well as instrument/quantity; `position_changes` is the trade subset. Existing event reconstruction test covers hold and roll. |
| 6 | Case repeats Core accounting | Requires Authority Change | Performance references Core daily/cumulative outputs; Result checks projection equality. Financial formulas have one canonical owner; worked oracles are verification examples. |
| 7 | W1 Slot transitions versus W2 rolls | Compatible | Policy resolves Slots on entry/expiry decisions only. A role change alone is no trade; authorized facade symbols and architecture tests preserve isolation. |
| 8 | Look-ahead risk | Compatible | Price-free current context, configuration-only Policy and current/future Close perturbation tests enforce price isolation. Metadata/active-set point-in-time availability is an explicit assumption, not a historical freshness proof. |
| 9 | Result / Online execution model | Requires Authority Change | Result consumes Core evidence plus Analyzer; Online composes the same path. Failure stage/category vocabulary follows Policy/Core/case ownership. No separate holding executor or ledger. Implementation remains WP4/WP5. |
| 10 | Completed work versus future Roadmap | Requires Authority Change | Package, Core and W2 synthetic adapter are present. Only remaining WP2–WP8 are active work; no package/simulator recreation or dual roadmap. |
| 11 | Duplicate / contradictory authority | Requires Authority Change | Entries navigate; specialized contracts own formulas and workflows. Current audit is separate from Roadmap. No previous-version authority or compatibility chain is maintained. |
| 12 | Residual implementation mismatch | Requires Authority Change | D1 explicitly separates mandatory Core daily-return output from passing existing tests. Missing later-WP deliverables are not mislabeled as regressions. |

No Blocking semantic decision is identified. DataLake integration, full Performance,
Result/Evidence, Online, HTTP/Web and real acceptance are **Deferred** to their assigned
WPs, not evidence of completed W2. Existing DataLake/W1 contracts and HTTP/Web planned
boundaries suffice; this reconciliation changes no producer contract or sibling code.

## Implementation drift register

### D1 — Core daily-return output

| Field | Current finding |
| --- | --- |
| Authority Requirement | [Core Accounting](../../core/ACCOUNTING.md) owns and exposes daily return, alongside cumulative PnL, Equity and cumulative return. Case must consume it unchanged. |
| Actual Code Behavior | `AccountingState` has no `daily_return`; `account()` computes only cumulative PnL, Equity and cumulative return. DailyRecord therefore cannot expose the required Core daily-return value. |
| Affected File / Symbol | [core/models.py](../../src/market_backtesting/core/models.py): `AccountingState`; [core/accounting.py](../../src/market_backtesting/core/accounting.py): `account`; `DailyRecord.accounting` consumers |
| Severity | High — required Core contract gap; blocks full accounting/Analyzer acceptance, but not starting Remaining WP2. No documented Daily PnL error. |
| Required Next Implementation Action | Add immutable Core daily-return output, initialize it to zero, compute it in `account()` with finite validation using the canonical contract, and project it unchanged into case analysis. Do not add a Case-side substitute. |
| Suggested WP | Remaining WP2, before Analyzer return projections |
| Acceptance / Test Evidence | Current static inspection confirms the missing field/calculation. Existing tests verify cumulative accounting, not the required output. Closure must cover initial/zero, positive and negative session returns, fixed InitialCapital versus previous Equity, finite arithmetic, sum of daily returns versus final cumulative return, and unchanged case consumption. No closure test or implementation is claimed here. |

No other mandatory mismatch is identified in the existing Core/W2 synthetic subset.
The register does not weaken full StateEvent reconstruction, causal price isolation,
real-instrument attribution or fail-without-partial-success requirements.

## Deferred and blocking decisions

- **Blocking: none.** Remaining WP2 can start by closing D1 under existing authority.
- **Deferred delivery:** Analyzer and both five-day case oracles (WP2), public facts
  integration/preflight (WP3), full Result/Evidence (WP4), Online mapping/store (WP5),
  HTTP/OpenAPI (WP6), Web (WP7), real IM and Windows Chrome → WSL acceptance (WP8).
- Historical metadata availability stays an explicit research limitation. Proving
  point-in-time availability or provider-current freshness is not implied by replay.
- Excluded features and platform/deployment limitations remain in
  [Roadmap](ROADMAP.md#deferred-and-known-limitations); no framework is prebuilt for them.

## Validation evidence

Validation records only commands actually run for this documentation reconciliation.
Existing synthetic acceptance cannot close D1 or validate future deliverables.

| Command / review | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | PASS — 105 tests, including Core oracle/event reconstruction, W2 causality and architecture/import isolation |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | PASS — 21 tests |
| `poetry run ruff check market_backtesting` | PASS |
| `poetry run mypy market_backtesting` | PASS — 19 source files |
| `poetry run python /tmp/hg_w2_authority_check.py` | PASS — temporary read-only audit of all 16 affected authority files: relative links/anchors, reachability from both root entries, unique canonical formula definitions, current terminology, static D1 confirmation and Markdown-only worktree |
| Concern/consumer and full-diff semantic review | PASS — one canonical owner per concern; public API/test agreement except registered D1; no W1/DataLake producer change or Core dependency expansion |
| `git diff --check` | PASS |
| Changed/untracked paths and staged diff review | Authority/Navigation Markdown only; no production code, tests, configuration or dependencies changed |
| Real DataLake acquisition, complete W2 Analyzer/case oracles, Online Store, HTTP runtime/OpenAPI integration, Web/browser and Windows Chrome → WSL E2E | NOT RUN — assigned to Remaining WP2–WP8 |

An initial combined pytest invocation over Backtesting and HTTP architecture tests
failed collection because both suites contain a non-package `test_architecture.py`.
The separate commands above are the module-prescribed invocations and passed without
changing tests or runtime code. The temporary audit script is outside the repository;
no new test tooling is introduced by this Markdown-only change.

Reconciliation Summary: **PASS** for authority consolidation and current-drift
registration. Core's full daily-return contract remains open as D1. Remaining WP2 is
ready to start with that correction, then the Analyzer; W2 delivery is incomplete.
