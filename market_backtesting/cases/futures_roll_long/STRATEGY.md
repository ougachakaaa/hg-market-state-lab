# Futures Roll Long strategy and holding simulation

This contract owns the position state machine, session decision order, real-contract
versus Slot identity, roll trigger and failure rules for the
[case](ARCHITECTURE.md). It does not own PnL formulas
([Accounting](ACCOUNTING.md)), upstream completeness ([Inputs](INPUTS.md)) or
result projection ([Result](RESULT.md)).

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

## Decision and accounting order

For each CFFEX session in strictly increasing order:

1. Validate the session's required Futures facts: the currently held contract's row,
   lifecycle and legal Close, and on a decision session the target's row and legal
   Close. Export completeness/public-fact validity and benchmark Index data are not
   strategy inputs; this stage performs no market I/O.
2. Attribute the session's PnL to the contract held from the previous session's
   close. Entry day PnL is zero. On a roll or final session, the PnL belongs to the
   old, still-held contract.
3. If this is the final session: close any position at the session Close, record the
   exit, terminate. Do not enter or roll.
4. If flat: resolve the session's Slots; select `M1`; validate that the target is
   active, has a legal Close and `delist_date > session`; enter at the Close. The
   session's PnL remains zero.
5. If holding and `session < delist_date`: continue holding. No decision-day Slot
   resolution is required.
6. If holding and `session == delist_date`: resolve the session's Slots; select the
   profile target (`M1` or `Q1`); validate the target; close the old contract at the
   Close and open the target at the same Close; record one roll. The new contract's
   PnL begins at the next session's close-to-close move.
7. If holding and `session > delist_date`: fail
   `held_contract_expired_without_roll`. Never continue an expired contract.

The final-session rule deliberately precedes entry/roll. A valid study window has at
least two sessions, so the first session cannot also be the final session. If a
future version admits a shorter window, it must define a new result contract; v1
does not invent a flat/no-holding-period result.

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

A failure is classified by the online application
([Online application](ONLINE_APPLICATION.md)); it never degrades into a partial
BacktestResult. Missing data is never treated as a closed session, zero price, zero
volume or an implicit empty active set.

## Required tests

WP1 must test at least:

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

No market data acquisition is required for WP1. Synthetic fixtures are sufficient and
preferred; WP3 adds the public-service integration and bounded real IM acceptance.
