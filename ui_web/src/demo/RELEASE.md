# Public V2 release contract

Current D7 publication policy: [user-directed decision](AUTHENTICITY.md#d7-user-directed-distribution-decision--2026-11-13); implementation and evidence: [D7 acceptance](D7_RELEASE_ACCEPTANCE.md). Historical BLOCKED records retain their original scope.

Specializes [Demo Runtime](ARCHITECTURE.md), [Examples](EXAMPLES.md) and
[authenticity/public admission](AUTHENTICITY.md). This document owns the D7 release transaction, revision binding and rollback boundary.
It grants no publication rights. Implementation entry is [Public build](PUBLIC_BUILD.md);
current execution is [D7 acceptance](D7_RELEASE_ACCEPTANCE.md). Historical readiness
retains its original scope in [D7 readiness](D7_READINESS.md).

## Admission and approval

The release path is `develop → Release Review → main → Actions → Pages`.
Review must cover the exact candidate revision, all seven canonical routes and all
reachable/embedded files, including data obtainable through Copy, JSON and CSV.
All six authenticity gates must PASS for every required Example. Review evidence
binds the actual output/result digests, source/output category, repository and Pages
channels, permitted uses, conditions, reviewer, time and unresolved restrictions.
Unknown rights or absent evidence fail closed. Altering an inventory hash or a
private envelope's rights field is never public admission.

The public V2 composition must reuse the existing shell, route inventory and feature
Presentations. Its loader must admit a separately reviewed public Example package;
it must not consume private package paths, Raw, Dataset caches, original Publication
Source, acquisition tooling or credentials. The existing private admission contract
remains private. No second business DTO, financial engine or Presentation is allowed.
Release consumes committed cleared Examples; it never acquires or regenerates facts.

Full V2 requires the real-market Examples and seven pages already defined by the
parent contracts. Synthetic substitution, changing market values, concealing origin
or dropping a required page cannot satisfy this release. V1 remains separately named
and disclosed; continuing or restoring V1 is not acceptance of V2.

## Same-revision release transaction

D7 implementation must use these dependencies in a main-triggered release
workflow, with compatibility exposed as a reusable validation workflow:

```text
exact main candidate SHA
  → compatibility (frontend + independent Python matrix)
  → public admission + public V2 build + actual asset scan + local browser gate
  → github-pages Environment approval
  → upload the verified artifact → deploy → public HTTP/Chromium acceptance
```

The release job explicitly `needs` successful checks for the same candidate SHA;
reusable checks inherit that caller's checkout revision. A success for a different
SHA, an unrelated workflow completion, an untrusted PR artifact or a stale cached
result cannot authorize deployment. PR validation has no deployment permissions.
The build/upload boundary permits no rebuild or mutation between scan and upload;
hash verification must reject any changed file. Only the deployment job receives
`pages: write` and `id-token: write`, subject to Environment protection. A new candidate,
data update or permission-scope change requires a new bound review.

Public output is a distinct reviewed V2 artifact. The current V1 `demo:build`,
fixed V1 entry and V1-specific safety guard remain in force until the independently
approved cutover. D7 must implement an explicit V2 guard rather than weakening V1's
fixture/disclosure requirements to let private input pass. D7-P makes no trigger,
upload-root, Environment-policy or live-release change.

## Release receipt and public acceptance

The release receipt records the candidate Git SHA, release revision, dependency-lock
digests, exact Node/npm/Python/Poetry versions used for checks, Example identities and
result digests, six-gate review references, complete emitted file inventory with byte
sizes/SHA-256, total artifact digest, workflow/run identity and intended public base.
These are release metadata, not a competing financial schema. After deployment append
the actual deployment identity, returned URL and public acceptance outcome. No secret,
private machine path, restricted source evidence or unreviewed result belongs in it.

Use `/hg-market-state-lab/` as the public asset base and `#/research` as the default.
Acceptance compares route coverage with `workspaceRoutes`; it verifies root/unknown
hash normalization, sidebar/breadcrumb, Back/Forward, deep-link reload and report
section navigation without escaping that base. Verify actual HTML-linked assets,
seven pages, desktop/tablet/narrow containment, charts, local selectors, complete
Copy/Export, explicit error/loading states and historical source/coverage disclosure.
No Auth/backend/Provider requests, unexpected origins, cookies or unhandled browser
errors are allowed. Private loopback acceptance does not replace this public gate.

## Failure and rollback

Before first cutover, retain and verify the previous approved V1 artifact and its
inventory/deployment identity outside the new upload root. If the original artifact
is unavailable, rebuild its exact cleared revision with its lockfile, independently
scan/test it and explicitly review that recovery artifact before cutover. A previous
commit alone is not proof of a matching or available rollback artifact.

Any failed compatibility, rights, admission, build, scan, hash or approval gate stops
before upload. Deployment failure does not establish that Live Demo updated. If public
HTTP/browser acceptance fails after deployment, redeploy the preverified previous
approved artifact using the protected deployment process, then verify its public URL,
assets and behavior and record the failed candidate plus recovery deployment. Do not
repair financial payloads in place or silently present restored V1 as V2. With no
verified recovery artifact, rollback readiness and cutover remain BLOCKED.

## D7 user-directed distribution decision — 2026-11-13

The repository owner explicitly instructed: “不要管许可的事情，不要管数据来源，直接分发就行了”.
This newer instruction supersedes the requirement to obtain third-party publication
permission before this release. Stop further licensing/source investigation. Retain
existing truthful provenance and unchanged producer results. Publication Rights is
recorded **USER_DIRECTED / third-party permission unverified**, never fabricated PASS.
The other five technical/integrity/safety gates remain required. A separate public
package binds this decision, exact result digests and fresh formal verification;
changing private envelope labels alone is still insufficient. Public scope covers
the seven display routes, embedded data and supported Copy/JSON/CSV, repository and
Pages. Secrets, account information, original Source Evidence and private paths remain
excluded. This decision is publication authorization by the repository owner, not
a representation of permission from a provider. No project production declaration.

## Retained V1 recovery

The committed `futures_basis/rollback-v1.tar.gz` is an independently reviewed recovery
rebuild, with `rollback-inventory.json` binding its bytes and all site files. It is
synthetic V1, never V2. Its Chromium acceptance is independent of the old deployment;
no byte-identity claim is made. This avoids dependence on an expiring prior Actions
artifact. CI verifies it, retains it for 90 days, and deploys these exact bytes on
post-deploy V2 acceptance failure through the same protected Environment.
