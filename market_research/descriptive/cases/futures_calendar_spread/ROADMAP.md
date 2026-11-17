# Calendar Spread delivery scope and limitations

Specializes [the case](ARCHITECTURE.md). L1 Daily Data and Historical Relative Value
are implemented through Python, Statistics, HTTP, Web and the static Demo.
Explicit execution now prepares missing required facts under [Inputs](INPUTS.md)
and [Application](APPLICATION.md); read-only query APIs remain export-only.
Completed implementation and acceptance records are available in Git history.

## Current boundaries

- Six Slot pairs and three metrics share the single [Definition](DEFINITION.md).
  Historical sampling, cutoff and interpretation remain in [Relative Value](RELATIVE_VALUE.md).
- [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md)
  and [Historical HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md)
  preserve distinct read-only and explicit execution permissions; synchronous execution
  uses shared capacity two, without a durable Run or generic scheduler.
- [Demo integration](../../../../ui_web/demo/CALENDAR_SPREAD.md) owns formal HTTP
  capture and shared Presentation. Local delivery does not imply publication.

## Deferred and unverified scope

L2 waiting value, L3 strategy validation, generic Plan/Batch/capability/Publication
admission and a CLI remain outside L1. Metadata is not proven point-in-time;
results describe historical Close relationships, not realized returns or trading advice.
Issue #13's bounded WSL/local-chain acceptance does not establish other deployments,
maximum 3660-date windows, prolonged load or cold-cache concurrent Source behavior.
No latency SLA or universal proxy-timeout suitability is claimed.
