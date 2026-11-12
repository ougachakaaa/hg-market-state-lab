# Futures Roll Long Mechanical Roll Position Policy

This contract owns W2 Mechanical Roll Position Policy for the [case](ARCHITECTURE.md).
Policy consumes current session, previous actual Portfolio, price-free current-session
Decision Context and immutable strategy configuration; returns an immutable Target
Portfolio. It never mutates actual state, executes a trade or computes PnL.
[Core Transition](../../core/PORTFOLIO_TRANSITION.md) owns all state evolution and PnL;
[Performance](PERFORMANCE.md) owns case analysis. References to trades below describe
the required consequences when Core consumes a W2 target, not a second case executor.

## Identity model

The strategy holds exactly one lot of a real, immutable `contract_code`. A position
is never keyed by a relative Slot. `M0`, `M1`, `Q1` and `Q2` are decision-day roles
provided by the published pure Slot resolution boundary. The same real contract can
change relative role while it is held; that does not create a trade.

W1 `ContractTransition` and `AbsenceBoundary` describe changes in descriptive Slot
mappings. They are not execution events. W2 does not call transition detection and
does not roll merely because the M1 mapping changed. A roll is triggered only when
the currently held contract's actual `delist_date` (last trading day, inclusive) is
the current CFFEX session.

`delist_date` is owned by DataLake Futures metadata. W2 must not infer expiry from a
delivery month, contract code, third-Friday rule, `last_delivery_date` or the W1
Observation calendar.

## Session calendar

The study calendar is the ordered set of CFFEX open sessions from the complete
public Calendar export for the inclusive request window. The session set:

- includes every CFFEX open date in the window, including an expiring contract's
  last trading day;
- excludes closed days; there are no synthetic calendar rows;
- must contain at least two sessions;
- defines the first session, final session and every roll opportunity.

The request dates are not required to be open sessions. The first valid session is
the entry decision; dates before it produce no strategy rows. The final session is the
termination decision. The observed session window must be reported separately from
the requested dates; it must never be relabelled as the requested window.

No weekday rule, holiday heuristic, `pretrade_date` inference or adjacent-day join
may supplement a missing Calendar. Calendar completeness and exact scope are
validated by [Inputs](INPUTS.md).

## Decision order

The Policy sees no current Close. Validate held real identity and lifecycle first;
expiry before the session fails even on the final session. Then apply these priorities:

1. Final session: return flat; never resolve Slots or roll. An unexpected flat previous
   state fails `no_position_on_final_session`.
2. First session with flat previous state: resolve M1 and return one-lot-long target.
   Flat on another non-final date fails `unexpected_flat_state`.
3. Held instrument before expiry: return the same one-lot target; no Slot resolution.
4. Held instrument on expiry: resolve its current M0 membership and profile M1/Q1
   target from the same validated active set; return the replacement one-lot target.

Target metadata must prove active lifecycle and remaining holding period, distinct
identity on roll and consistent multiplier. Core validates execution prices after
Policy decides. Replay alone advances dates and state, then accounts/records each day.

## State machine

| State | Guard | Transition / output |
| --- | --- | --- |
| `FLAT` | first non-final session | `HOLDING(entry contract = session M1)`, entry execution |
| `HOLDING` | non-delist, non-final session | `HOLDING`, no execution |
| `HOLDING` | session is `delist_date`, non-final | `HOLDING(new profile target)`, close + open executions, one roll |
| `HOLDING` | final session | `FLAT`, close execution, no new position |
| `HOLDING` | session > `delist_date` | failure `held_contract_expired_without_roll` |
| `FLAT` | final session | unreachable in v1; if reached, failure `no_position_on_final_session` |

Terminal postconditions: the final session ends flat; no execution occurs after the
final close; the result contains exactly one entry, exactly one exit, and exactly one
roll for each held-contract expiry before the final session (zero rolls when no expiry
occurs inside the window).

## Entry

- Entry contract is the first session's `M1` mapping.
- The contract must be an active ordinary contract on that session, with a legal
  `Close > 0` and `delist_date > entry session`.
- The strategy buys one lot at the entry session's Close. PnL on the entry session
  is zero because there is no prior strategy close.
- If the first session has no active contract, no `M1` mapping, an irregular active
  set, or a target without a remaining holding period, the backtest fails. It never
  substitutes another product, month, contract or adjacent date.

## Holding

- The held contract is identified by its exact `contract_code`; no daily Slot
  re-selection occurs.
- The contract must remain active and present with a legal Close on every session
  from entry through its `delist_date` or the final session, whichever comes first.
- Contract metadata (product, underlying, delivery month, multiplier, `list_date`,
  `delist_date`) must remain consistent across the retained export. A changed
  metadata version or identity conflict fails the backtest; it does not silently
  update a position.
- A held contract's relative Slot may change while held. That is not an execution
  event and does not change position size.

## Roll

- The trigger is `session == held_contract.delist_date`, inclusive. The expiry session
  is still a valid trading session and must contain the expiring contract's row and
  Close.
- The old contract must be present in the same complete decision-session active set
  and must resolve to `M0`. This is the validated consequence of the expiring contract
  being the front contract; it is not inferred from the contract code, delivery month
  or a previous role. If the old contract is absent or maps to another Slot, fail
  `invalid_contract_lifecycle`; do not emit a roll from a role change.
- The target Slot is determined by the strategy profile using that same session's
  complete active set: `M1` for `expiry_to_M1_v1`, `Q1` for `expiry_to_Q1_v1`.
- The target must be active on the decision session, have a legal `Close > 0`, a
  `delist_date > session`, and must not be the old contract.
- The old contract is sold at the old contract's Close. The new contract is bought at
  the new contract's Close. Both prices are the same session's ideal Close prices;
  they are not required to be equal across contracts.
- No PnL is created by the difference between the old and new contract prices. The
  session's PnL is entirely the old contract's close-to-close change. The new
  contract starts from its roll Close.
- If `delist_date` falls inside the study window but is not a CFFEX session, the
  backtest fails. W2 does not roll on the next open session, because that would hold
  past the actual last trading day.
- If the held contract's `delist_date` is after the final session, no roll occurs; the
  final session closes the position at its Close.

## Termination

- The final study session closes the currently held contract at that session's Close.
- The final session does not enter, roll or establish any position with no holding
  period. If the final session is also the held contract's `delist_date`, the contract
  is closed and no replacement is opened.
- The final result is flat after the close. Daily rows still attribute the final
  session's PnL to the contract that was held during the session; the result's
  end-of-session position on the final row is null.
- There is no next-session PnL, overnight position or post-study execution.

## Failure rules

The operation fails closed, produces no successful result and does not silently
repair or continue when any of the following is true:

- Calendar incomplete, ambiguous, outside the exact requested window, or containing
  fewer than two CFFEX open sessions;
- Futures coverage incomplete for the product or any CFFEX session in the window;
- Index coverage incomplete or missing a Close for any CFFEX session;
- Decision session active set missing, duplicated, conflicting or structurally
  invalid under the authorized Slot resolver;
- Entry/roll target absent, not active, already expired, equal to the old contract or
  lacking a remaining holding period;
- Held/entry/roll contract row missing, duplicated, outside scope, or with
  inconsistent product/underlying/delivery-month/lifecycle metadata;
- Price missing, non-finite, `<= 0`, or an illegal value that cannot be used as the
  ideal Close;
- Multiplier missing, non-positive or inconsistent with the entry contract;
- `delist_date` missing/invalid or, when inside the study window, not a CFFEX session;
- Underlying index identity inconsistent across Futures rows or with the Index
  export;
- Session count, price, equity or result arithmetic becomes non-finite or invalid.

Pure Policy/replay failures retain the public Core/case category and reason. The
[Online application](ONLINE_APPLICATION.md) projects them with execution-stage context;
a failure never degrades into a partial BacktestResult. Missing data is never treated
as a closed session, zero price, zero volume or an implicit empty active set.

## Required tests

Required Policy/Core/integration coverage:

- first-session entry at M1; both profiles;
- normal holding and final-session exit;
- expiry-day inclusion, roll at the expiry close, next-session new contract;
- final session equal to expiry: close only, no new position;
- no roll when expiry falls after the final session;
- W1 Slot mapping change while holding a different real contract: no trade;
- missing/irregular decision metadata, duplicate identity/month, metadata conflict;
- held contract expiry without roll, target equal to old, target already expired;
- missing contract row/price, non-positive or non-finite Close;
- Calendar/Futures/Index scope, completeness and underlying inconsistencies;
- deterministic ordering and immutable inputs.

Pure policy/replay acceptance uses synthetic fixtures without market acquisition.
WP3 adds public-service integration and bounded real IM acceptance; current completion
is recorded in the [roadmap](ROADMAP.md).

## Decision evidence and Python boundary

`MechanicalRollPolicy` stores product/profile configuration only. `DecisionContext`
contains first/final flags, current metadata/instrument references and optional current
active-set evidence; no price, Snapshot, full calendar or future facts. The target
retains decision reason, selection Slot, validated old Slot on a roll and source ref.
`replay_futures_roll(FuturesRollInput)` prepares synthetic contexts/snapshots, derives
capital using [Performance](PERFORMANCE.md), calls Core Replay once and projects
executions/rolls from recorded Core events. It returns `FuturesRollReplay`, not the
future full BacktestResult. There is no legacy holding-only execution API.
