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

Transition selects required quotes from the supplied read-only snapshot using the
Previous and Target Portfolio's real instrument IDs: the previous instrument for
valuation/closure, the target instrument for opening or continued holding. Validate
all required quotes before returning a result. A Slot or target replacement cannot
change which incoming instrument owns today's PnL; the next session values the real
instrument retained in Next Portfolio.

For the position held entering the session, the unique formula is:

```text
DailyPnL = (CurrentClose - PreviousReferencePrice) × PreviousQuantity × Multiplier
```

CurrentClose and PreviousReferencePrice must belong to the same real instrument.
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
`TransitionResult.events` is the complete StateEvent sequence. Starting with Previous
Portfolio, each event's `before` must match the current position; applying its `after`
in order must reconstruct Next Portfolio exactly, including reference price and
valuation date. An unchanged holding therefore still records a `mark`; flat-to-flat
has no events and reconstructs the same flat Portfolio.

`TransitionResult.position_changes` is only the close/open subset used to project
real executions. A roll has ordered close then open legs; `mark` never counts as a
trade. This subset alone is insufficient for no-trade valuation reconstruction and
must not replace the complete events in retained replay evidence. Events are evidence
only, not an event bus or order lifecycle.
