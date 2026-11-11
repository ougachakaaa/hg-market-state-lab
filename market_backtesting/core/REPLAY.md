# Daily replay, policy causality and recorder

This contract specializes [Core](ARCHITECTURE.md). `replay(sessions, policy,
initial_capital, assumptions)` consumes immutable ordered `ReplaySession` inputs,
each associating a date, decision context and valuation/execution snapshot. Validate
nonempty, unique, increasing date-only sessions and matching snapshot dates.

Initial Portfolio is flat. For every session, including sessions without a trade,
Replay coordinates the following ordered operations:

1. Read Previous Portfolio from the prior session.
2. Call `policy(session, previous_portfolio, decision_context)` for Target Portfolio.
3. Hand Previous/Target and this session's snapshot to Transition; their real instrument
   identities determine the required valuation and execution quotes.
4. Transition values the Previous Portfolio and computes its Daily PnL.
5. Transition applies the target conversion at the close.
6. Transition returns Next Portfolio and ordered state/price evidence.
7. Accounting consumes that Transition once and accumulates the accounting state.
8. Recorder retains the daily evidence, then Next Portfolio becomes the following
   session's Previous Portfolio.

`ReplaySession.snapshot` can contain additional validated instrument facts. Preparing
that snapshot is the input adapter's responsibility; selecting required quotes inside
it is Transition's responsibility. Replay coordinates consumption without a second
selection service or market-data framework. Accounting performs no market lookup.
Strategy configuration is bound in the callable policy. Replay owns sequencing and
failure propagation, not strategy rules, formulas or benchmarks.
A fixed positive quantity is established by the first non-flat target and must not
change later, including after a flat interval.

## Decision-time boundary

Replay may preload historical snapshots. It passes only the explicitly supplied
price-free decision context to Policy, never a Snapshot, session collection or future
prices. A case must publish the decision-time meaning of its context and restrict its
policy to facts admissible at that time. Preloading the full history grants no future
information access. The previous actual Portfolio necessarily carries its prior valuation.
Known calendars and contract metadata are admissible under explicit point-in-time
assumptions; no Source freshness claim is inferred from historical preload.

## Recorder and failures

Recorder builds an immutable tuple of `DailyRecord`: date, previous Portfolio, target,
Transition with pricing evidence and ordered events, next Portfolio and daily/cumulative
AccountingState. `ReplayResult` also retains assumptions and initial capital.
There is no filesystem persistence or Online Run identity. Errors propagate with
category/reason and available date/instrument context; no successful partial result is
returned. A policy error is not silently caught, retried or converted to a flat target.
