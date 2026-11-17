# Futures Roll Long delivery scope and limitations

Specializes [the case](ARCHITECTURE.md). Position-Driven Core V1, M1/Q1 Policy,
public DataLake preparation, result/evidence/reproduction, online SQLite execution,
authenticated HTTP and Web delivery are implemented. No W3 or production delivery
is implied. Completed work packages and acceptance records remain in Git history.

## Acceptance boundaries

Pure Core replay and case five-day Performance oracles are independent.
Full StateEvent reconstruction, real-instrument attribution, causal price isolation,
complete public inputs and failure without partial success remain binding under
[Inputs](INPUTS.md), [Performance](PERFORMANCE.md), [Result](RESULT.md) and
[Evidence](EVIDENCE.md). Online composes that same execution path; HTTP and Web
own delivery only. Preflight is advisory and does not initialize storage.
The original integrated gate covered both IM profiles over 2024-01-01..2026-10-30
with CSI1000 Buy & Hold and Windows Chrome accessing the WSL authenticated workflow;
this historical scope is not a fresh runtime verification claim.

## Deferred and known limitations

- Historical metadata and active-set decision-time availability is an explicit replay
  assumption, not proven point-in-time Source freshness. Complete exports and memory
  preload do not grant Policy future information access.
- IF/IH/IC retain semantic/synthetic coverage; real acceptance beyond IM is deferred.
- Fees, slippage, margin, funding, ETF comparison, Sharpe/risk-adjusted metrics,
  annualization, optimization and other exclusions remain outside W2 as defined by
  [Performance](PERFORMANCE.md#exclusions-and-forbidden-interpretations).
- Online list/history, cancel/delete/retry, idempotency keys, queueing, multi-process
  execution, automatic cleanup/TTL, standalone online evidence/replay endpoints,
  result CSV/copy/export and production SLA remain outside this release.
- Full canonical evidence/replay is implemented in WP4; the online result exposes its summary.
- The portable SQLite online store supports native Windows, Linux, WSL2 and Linux Docker
  on local filesystems. Native non-WSL Linux storage and privileged Windows symlink
  branches remain unverified; see [Online storage](ONLINE_STORAGE.md#platform-verification-boundary).
  Production deployment remains NOT_VERIFIED; no production ingress, packaging or SLA is claimed.
- Provider freshness/correction/TTL semantics remain DataLake-owned. HTTP wire details
  and Web generated artifacts belong to WP6/WP7, not this authority reconciliation.
