# Daily replay, policy causality and recorder

This contract specializes [Core](ARCHITECTURE.md). `replay(sessions, policy,
initial_capital, assumptions)` consumes immutable ordered `ReplaySession` inputs,
each associating a date, decision context and valuation/execution snapshot. Validate
nonempty, unique, increasing date-only sessions and matching snapshot dates.

For every session, including sessions without a trade, Replay passes the previous
actual Portfolio to `policy(session, previous_portfolio, decision_context)`, consumes
its immutable Target Portfolio through Transition, passes the result to Accounting,
records the daily result, then hands the new Portfolio to the next session. Strategy
configuration is bound in the callable policy. Replay owns sequencing and failure
propagation, not strategy rules, formulas or benchmarks. Initial Portfolio is flat.
A fixed positive quantity is established by the first non-flat target and must not
change later, including after a flat interval.

## Decision-time boundary

Replay may preload historical snapshots. It passes only the explicitly supplied
price-free decision context to Policy, never a Snapshot, session collection or future
prices. W2's published context contains current metadata/active-set evidence and
first/final-session flags only. Its Policy retains configuration only, not market
prices. The previous actual Portfolio necessarily carries its prior valuation.
Known calendars and contract metadata are admissible under explicit point-in-time
assumptions; no Source freshness claim is inferred from historical preload.

## Recorder and failures

Recorder builds an immutable tuple of `DailyRecord`: date, previous Portfolio, target,
Transition with pricing evidence and ordered events, next Portfolio and cumulative
AccountingState. `ReplayResult` also retains assumptions and initial capital.
There is no filesystem persistence or Online Run identity. Errors propagate with
category/reason and available date/instrument context; no successful partial result is
returned. A policy error is not silently caught, retried or converted to a flat target.
