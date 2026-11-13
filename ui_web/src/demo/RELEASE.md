# Public V2 release contract

Specializes [Runtime](ARCHITECTURE.md), [Examples](EXAMPLES.md) and
[Authenticity](AUTHENTICITY.md). Owns the release transaction, revision binding and
rollback. [Public build](PUBLIC_BUILD.md) owns packaging/tooling; [D7 acceptance](D7_RELEASE_ACCEPTANCE.md)
owns execution evidence. Publication policy has one canonical owner:
[the current user-directed decision](AUTHENTICITY.md#d7-user-directed-distribution-decision--2026-11-13).

## Admission and review

The release path is `develop → Release Review → main → Actions → Pages`.
Review covers the exact candidate, all seven canonical routes and every reachable or
embedded file, including Copy/JSON/CSV. The five technical authenticity/integrity/safety
gates must PASS. Publication Rights is USER_DIRECTED under the explicit owner decision;
third-party clearance remains unverified and must not be represented as PASS.
Review binds exact result digests, source/output categories, repository/Pages channels,
conditions, reviewer/time and the distribution decision. Missing records fail closed.
A private envelope label change is insufficient for independent public admission.

The public composition reuses the shared static shell, route inventory and formal
feature Presentations. It consumes a separately reviewed committed package, never
private package roots, Raw, caches, original Publication Source or credentials.
No second business DTO, financial engine or Presentation is allowed. Release never
acquires data or regenerates results. Full V2 requires all specified real-market
Examples and seven pages; synthetic substitution or a reduced page set does not pass.
V1 remains independently named and disclosed, including on recovery.

## Same-revision transaction

```text
exact main SHA
  → reusable compatibility (frontend + independent Python matrix)
  → public admission + build + actual asset scan + local Chromium
  → protected github-pages Environment
  → verify unchanged bytes → upload → deploy → public HTTP/Chromium acceptance
```

Explicit `needs` dependencies bind checks to the same checkout revision. An unrelated
workflow success, stale SHA or untrusted PR artifact cannot authorize deployment.
PR checks have no Pages/OIDC permissions. Only the protected deploy job receives them.
The official workflow triggers main only; develop compatibility never updates Pages.
Existing Environment rules must be inspected, enforce deployment-branch protection
and permit main. Preserve required approvals; do not bypass or weaken settings.

No rebuild or asset mutation is allowed between final scan and upload. Verify the
complete file set, sizes and hashes again after transfer to the deployment job.
Public V2 uses its own output root/guard. The existing V1 entry, fixture and safety
checks remain independent. Missing public admission records BLOCKED and prevents V2
publication; a present invalid package fails. Neither outcome is successful V2 release.

## Receipt and acceptance

Retain source SHA, dependency-lock digests, check/build toolchain versions, Example
identities/result digests, review bindings, complete file sizes/SHA-256, artifact digest,
workflow/run identity and public base. Check logs and release artifacts jointly retain
validation toolchain and build details. After deployment record the actual Pages URL,
run, release SHA and online acceptance outcome. No private evidence belongs in receipts.

Use `/hg-market-state-lab/`, with `#/research` default. Chromium compares routes with
`workspaceRoutes`: root/unknown normalization, seven pages, deep reload, sidebar,
breadcrumbs, Back/Forward, 1440/1024/390 layouts, all report sections, Plotly
Hover/Zoom/Pan/Reset, local selectors, M1/Q1, Analysis/Views and complete Copy/CSV/JSON.
Verify source/coverage/producer disclosure and bilingual disclaimer. No API/Auth/Provider
requests, unexpected origins, cookies or browser errors are allowed. Online acceptance
also compares every deployed file to the scanned inventory, allowing bounded CDN
propagation before failing. Loopback acceptance does not establish public availability.

## Failure and recovery

Any failed compatibility, admission, build, safety, hash or required approval gate stops
before publication. Deployment success alone does not establish online acceptance.
The committed [V1 recovery inventory](futures_basis/rollback-inventory.json) binds an
independently reviewed synthetic recovery rebuild and `rollback-v1.tar.gz`. It is
not asserted byte-identical to the previous deployment. Local V1 Chromium and asset
review validate the recovery before cutover; its availability does not depend on an
expiring old Actions artifact. Verify archive and expanded bytes before use, retain
with the release for 90 days, and never mutate it during recovery.

On post-deployment acceptance failure, restore those exact verified V1 bytes through
the protected deployment job, verify the restored URL, all assets and V1 behavior,
retain the failure/recovery receipt and fail the V2 release. Restored V1 is never a
passing substitute for V2. Do not patch financial payloads in place.
