# market_statistics Agent Rules

Inherit the root [AGENTS.md](../AGENTS.md). Read the
[repository architecture](../ARCHITECTURE.md), then [module authority](ARCHITECTURE.md)
for identity/dependencies and [public contract](CONTRACT.md) for numerical semantics.
Read only the relevant method authority, [Quantile](QUANTILE.md) or
[IntervalCount](INTERVAL_COUNT.md) or [Mean](MEAN.md), and [BACKEND.md](BACKEND.md) for numerical library
selection, adaptation, result validation and upgrades. Libraries are implementation
dependencies, not an alternate source of public statistical meaning.

Update the narrowest canonical authority before implementation. Resolve pending method
decisions explicitly; do not infer defaults from statistical convention, old code or user
silence. Statistics must not depend on Research, DataLake, Snapshot, Modeling or inbound
UI modules, acquire market facts, or take ownership of consumer conversion and interpretation.

STAT-IMP-01 implements the public Python package, both V1 methods and root package
registration under the existing contracts. No CLI or HTTP service is published. Do not
create a module-local Python environment, statistical framework or compatibility layer.
Authority readiness is not runtime readiness.

## Scoped verification

Follow the [root verification policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).
Select only directly affected business test files/cases. No default full-module or
cross-module regression, topology, browser, live-data or deployment acceptance.
Retain business invariants and fixtures; record unavailable checks as NOT VERIFIED.
Do not modify real market data or caches to satisfy tests.
