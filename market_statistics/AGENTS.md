# market_statistics Agent Rules

Inherit the root [AGENTS.md](../AGENTS.md). Read the
[repository architecture](../ARCHITECTURE.md), then [module authority](ARCHITECTURE.md)
for identity/dependencies and [public contract](CONTRACT.md) for numerical semantics.
Read only the relevant method authority, [Quantile](QUANTILE.md) or
[IntervalCount](INTERVAL_COUNT.md), and [BACKEND.md](BACKEND.md) for numerical library
selection, adaptation, result validation and upgrades. Libraries are implementation
dependencies, not an alternate source of public statistical meaning.

Update the narrowest canonical authority before implementation. Resolve pending method
decisions explicitly; do not infer defaults from statistical convention, old code or user
silence. Statistics must not depend on Research, DataLake, Snapshot, Modeling or inbound
UI modules, acquire market facts, or take ownership of consumer conversion and interpretation.

Current scope is authority only: no Python package, method implementation, package
registration, CLI or HTTP service. Do not create a module-local Python environment,
statistical framework or compatibility layer. Authority readiness is not runtime readiness.

Run applicable checks from the repository root's unique Poetry environment:

```bash
poetry run pytest market_research/tests
poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_research
poetry run mypy market_research/tests
poetry run ruff check data_snapshot/tests/test_authority_topology.py
poetry run mypy data_snapshot/tests/test_authority_topology.py
git diff --check
```

Check relative links/anchors, root reachability, unique semantic ownership and the complete
diff. Future runtime work must add appropriate behavior verification once its contracts
are settled; current architecture checks do not establish statistical correctness.
The separate STAT-IMP-01 must explicitly declare NumPy in the root project with a tested
Python-compatible range and prove method conformance; STAT-01 adds neither that dependency
nor a runtime. Keep future acceptance obligations distinct from actually executed checks.
