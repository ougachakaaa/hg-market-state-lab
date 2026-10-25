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

STAT-IMP-01 implements the public Python package, both V1 methods and root package
registration under the existing contracts. No CLI or HTTP service is published. Do not
create a module-local Python environment, statistical framework or compatibility layer.
Authority readiness is not runtime readiness.

Run applicable checks from the repository root's unique Poetry environment:

```bash
poetry run pytest market_statistics/tests market_research/tests
poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_statistics market_research
poetry run mypy market_statistics/src market_statistics/tests market_research/tests
poetry run ruff check data_snapshot/tests/test_authority_topology.py
poetry run mypy data_snapshot/tests/test_authority_topology.py
git diff --check
```

Check relative links/anchors, root reachability, unique semantic ownership and the complete
diff. Runtime changes must run numerical and failure-injection tests; architecture checks
alone do not establish statistical correctness.
NumPy is declared in the root project with a tested Python-compatible range. Backend
upgrades must prove method conformance. STAT-01 added neither that dependency nor a
runtime; STAT-IMP-01 supplies runtime evidence. Keep obligations distinct from executed checks.
