# Futures Basis delivery scope and remaining verification

Specializes [the case](ARCHITECTURE.md). Pure Slot resolution, public input preparation,
observations, descriptive statistics, offline report/evidence, online execution,
read-only preflight, HTTP and Web consumers are implemented.
The online application exclusively uses [case-owned SQLite](ONLINE_STORAGE.md).
Completed work packages and their execution records remain in Git history.

## Known gaps and defer

- Complete Futures proof is required; the public service does not expose independent
  active catalogs for failed dates. Partial Futures needs a new upstream decision.
- R01-A is not admitted to Publication V1, Research Explorer or generic
  capability/Plan/Batch execution. Snapshot's simple annualized percentage and this
  case's log/decimal/D=0 Not Applicable convention are distinct; old results cannot
  be relabeled or converted by sign or unit adjustment alone.
- Full canonical inputs, associations and replay belong to the
  [offline evidence package](EVIDENCE.md). Online exposes the versioned reader projection,
  fingerprint and coverage; online evidence/replay endpoints remain deferred.
- Run list/history, delete/cancel, queue/fair scheduling, multi-process execution,
  automatic cleanup and POST idempotency remain outside the online scope.
- No default historical study window, provider-freshness guarantee or SLA is implied.

## Verification boundaries

Original integrated acceptance covered bounded real IM and the WSL local chain;
Windows Chrome and Nginx/production deployment remain unverified for that case gate.
Later storage acceptance covered native Windows, WSL2 and Linux Docker, independently
of browser acceptance; native non-WSL Linux and privileged Windows symlink branches
remain unverified. See [storage trust boundary](ONLINE_STORAGE.md).
Use current [usage](USAGE.md) and [preflight](PREFLIGHT.md) contracts; historical
PASS never establishes current backend, cache, Source or deployment readiness.
