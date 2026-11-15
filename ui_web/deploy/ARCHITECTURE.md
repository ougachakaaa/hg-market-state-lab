# Demo release authority

Specializes [Demo authority](../demo/ARCHITECTURE.md). WSL Online publishing remains
independent; publish.py is not a Pages deployment mechanism.

## Build identity and receipt

The sole offline build consumes an admitted private snapshot. Its completion marker
records the snapshot Manifest SHA-256 and actual Git HEAD. Release requires those
identities to match the confirmed checkout and Git-tracked Manifest bytes.
A receipt outside the site records format, sourceCommit, manifestSha256, files
(path, size, SHA-256) and artifactDigest (SHA-256 of the serialized sorted file list).
Independent verification recomputes all bytes and checks externally expected identity.
The receipt is integrity evidence, not a signature or financial accuracy guarantee.

Only completed artifacts with local referenced assets under /hg-market-state-lab/
are accepted. Reject symlinks, nonregular files, maps, credentials, private paths,
fixtures and forbidden runtime dependencies. Vite checks its actual module graph;
verification independently checks the emitted dependency inventory.

## CI and publication

DDB-06 publisher contract: `npm run demo:publish` selects fetched remote-main,
never implicit HEAD. The configured default remote is github; --remote selects another
GitHub remote explicitly. Feature/develop/main own development/integration/approval;
release/demo-pages is only an FF deployment pointer, without release-only commits.
The publisher rejects dirty relevant sources, local-main drift, non-main candidates,
divergent release history and active/uncertain deployments. It uses a clean detached
worktree for dependency installation and the complete release gate, then checks remote
refs again and performs only a normal explicit-SHA push. Git's FF check is the final
server-side safeguard; local preflight cannot prohibit manual pushes or atomically lock
remote main. CI independently rejects non-main history. No force push is permitted.
Existing release HEAD uses existing run/deployment evidence without implicit reruns.
Polling has finite deadlines; failures after push never imply successful publication.
Online verification uses the anonymous Playwright browser network stack to read and
hash every emitted file against the CI receipt before route-level browser
acceptance. Gate evidence and receipt are retained outside the public site.

Manual offline CI accepts feature branches without deployment permissions. Ordinary
push checks stay lightweight. Pages runs only on release/demo-pages pushes. The exact
triggering SHA must be reachable from freshly checked-out remote-main history.
Checkout is pinned to that SHA; Linux independently runs the complete release gate.
Build and verify once, transfer the site and separate receipt, then independently
verify downloaded bytes before upload-pages-artifact. Deploy the exact uploaded
artifact selected by its unique run/attempt name without rebuilding or fetching business data. Failed checks or Environment
rejection stop publication without fallback. Use github-pages Environment and pages
concurrency, with Pages/OIDC permissions confined to the deployment job.

Inspect existing Pages, Environment branch protections and Actions permissions before
actual release; unavailable inspection is reported truthfully. Root personal-study
policy applies. Preserve original sources and investment disclaimers. No data-rights
gate is introduced. CI acceptance and actual deployment are reported separately.
