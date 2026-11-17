# Futures Basis delivery scope and remaining verification

Specializes [the case](ARCHITECTURE.md). Pure Slot resolution, public input preparation,
observations, descriptive statistics, offline report/evidence, online execution,
read-only preflight, HTTP and Web consumers are implemented.
The online application exclusively uses [case-owned SQLite](ONLINE_STORAGE.md).
Completed work packages and their execution records remain in Git history.

## Distribution V2 handoff

WP2 implements the four-metric backend with definition `futures_basis_definition_v2`,
reader `futures_basis_report_evidence_v2` and online profile `r01a_standard_v2`.
The manifest remains `futures_basis_report_manifest_v1`; canonical input bytes and
fingerprints retain their existing contract. Frontend readers/presentation remain
V1 pending WP3 and cannot consume V2 results yet; the current Demo Bundle remains
a WP5 recapture dependency. This is not publication readiness.
These package names refer to Distribution V2, independently of historical WP numbers.

- WP2 (implemented) — the fourth metric through Observation, Accounting, formal analyses,
  Report/History, Evidence/Reader and HTTP, including exact profile/definition
  associations and generated-contract updates. Do not redefine the first three metrics.
- WP3 — shared frontend fourth Metric, width presets and boundary formatting under
  [Distribution presentation](../../../../ui_web/src/features/futures_basis_research/DISTRIBUTION.md).
- WP4 — full-population validation, local rank-based trimming, Histogram and complete
  exclusion audit, with deterministic edge-case and conservation tests.
- WP5 — recapture the formal Basis Bundle, update the unique active Manifest, perform
  end-to-end acceptance and separately authorized integration/release. No legacy
  adapter is required to preserve disposable development payloads.

WP1 does not implement, test business runtime, regenerate contracts/Bundles, clean
stores, merge or publish. No new permanent implementation diary is introduced.

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
