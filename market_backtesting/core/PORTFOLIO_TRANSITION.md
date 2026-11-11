# Portfolio and daily transition

This is the canonical state, event and Gross Daily PnL contract of [Core](ARCHITECTURE.md).

## Immutable carriers

`InstrumentReference` carries real instrument identity, positive finite multiplier
and nonempty provenance. `Position` adds fixed positive quantity, previous reference
price and valuation date. `Portfolio` contains zero or one Position.
`TargetPortfolio` contains zero or one target instrument/quantity, plus immutable
policy decision evidence (reason, optional selection role and source association).
A policy returns a target; it cannot mutate actual state or calculate executions/PnL.

`DailyMarketSnapshot` contains one session's unique instrument Close quotes and
nonempty pricing provenance. Quotes must be numeric (not bool), finite and positive.
Missing required quotes, duplicate identities, invalid multiplier/reference/quantity,
identity conflicts or non-finite arithmetic fail explicitly. V1 rejects quantity
changes across a run; it has no short or multi-instrument target.

## Transition and assumptions

`transition_portfolio(previous, target, snapshot, assumptions)` accepts explicit
execution and valuation assumptions. V1 supports only same-session ideal Close
execution and Close valuation. A previous valuation date must precede the session.

For the position held entering the session, the unique formula is:

```text
DailyPnL = (CurrentClose - PreviousReferencePrice) × PreviousQuantity × Multiplier
```

A flat previous state contributes zero. Transition then applies target changes:
close the old instrument before opening a replacement. The replacement starts at its
own execution Close; the cross-instrument price gap never contributes PnL. An unchanged
holding emits no trade but updates its reference and valuation date every session.
Flat-to-flat emits no trade and contributes zero. A replay need not end flat; case
policy owns terminal targets.

## Evidence and events

Transition returns previous/target/next states, session, assumptions, snapshot,
Daily PnL and pricing evidence (instrument, previous reference, current valuation,
quantity and multiplier). It retains ordered immutable state events with before/after
Position values: mark the incoming position, close it if needed, then open the target.
Position Change Events are the close/open subset; valuation updates are never trades.
Applying all state events to Previous Portfolio reconstructs Next Portfolio, including
no-trade sessions. Events are evidence only, not an event bus or order lifecycle.
