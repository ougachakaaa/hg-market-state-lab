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

Manual offline CI accepts feature branches without deployment permissions. Ordinary
push checks stay lightweight. Pages is workflow_dispatch only on main; the required
full confirmed source SHA must equal the dispatch SHA. Checkout is pinned to that SHA.
Build and verify once, transfer the site and separate receipt, then independently
verify downloaded bytes before upload-pages-artifact. Deploy the exact uploaded
artifact selected by its unique run/attempt name without rebuilding or fetching business data. Failed checks or Environment
rejection stop publication without fallback. Use github-pages Environment and pages
concurrency, with Pages/OIDC permissions confined to the deployment job.

Inspect existing Pages, Environment branch protections and Actions permissions before
actual release; unavailable inspection is reported truthfully. Root personal-study
policy applies. Preserve original sources and investment disclaimers. No data-rights
gate is introduced. CI acceptance and actual deployment are reported separately.
