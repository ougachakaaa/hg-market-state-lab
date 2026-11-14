# WP1A execution evidence - 2026-11-13

Baseline: `5f347a09aed0ee06fd1849ad577a2218a4a58050`; same working branch,
no merge, push or deployment. Semantic reconciliation commit: `b6e2857`.

## Scope and paths

Authority: STRUCTURE, STRUCTURAL_MIGRATION and STRUCTURAL_INVENTORY reconcile one
Demo generation, Manifest/hash-only future Bundle admission and seven complete Result Bundles.
Current admission assertions remain unchanged. No runtime/data/test source moved or retired.

| Previous output | Current output |
| --- | --- |
| dist | .build/online |
| dist-demo-public | .build/demo (site, receipt, browser evidence) |
| dist-demo | .build/tests/v1 |
| dist-demo-shell | .build/tests/shell |
| dist-{option-chain,premium,catalog,explorer,futures-basis,backtesting}-test | .build/tests/<suite> |
| OS-temp static-contract-* build | .build/tests/static-contract-* (removed after probe) |
| node_modules/.tmp TypeScript build info | .build/cache |
| Vite configurable cache | .build/cache/vite or vite-demo |

Vite preview reads the same configs. npm scripts retain their commands and route through
updated configs/helpers. Private --output and offline report delivery are explicit external
contracts; browser/backend OS-temp roots are execution/evidence directories, retained.
Dependencies and third-party caches remain npm-owned. One root package/lock remains.
Pages upload/download/verification paths agree; hidden-file inclusion supports the new hidden
parent. Triggers, permissions, Environment, retention and publication strategy are unchanged.
Local deployment template agrees with Online output; deployment was not executed.

## Verification

| Check | Result |
| --- | --- |
| contract:check | PASS |
| build | PASS; existing large-chunk warnings |
| lint | PASS |
| demo:build (V1) | PASS |
| Seven specialized static builds | PASS: shell, option-chain, premium, catalog, explorer, futures-basis, backtesting |
| test:static-compatibility | PASS; actual V1/private/public entry graph builds |
| npm run test | BLOCKED; reproduced WP0 RUN-only behavior before output edits and after migration; no suite results. Threads probe also RUN-only. Invocations stopped; no assertions disabled |
| demo:build:public | BLOCKED before output generation: Review evidence digest mismatch |
| test:public-safety | BLOCKED: existing reviewed payload byte mismatch |
| Eight affected browser suites | BLOCKED at Chromium launch after successful build/graph checks; required chromium_headless_shell-1248 absent |
| Chromium installation attempt | BLOCKED: download remained at 0 percent, stopped without changing browser assertions |
| Python tooling | 15 passed, 2 failed (existing private WPA isolation/Windows URI issues); treat these two checks as BLOCKED for acceptance |
| Python deployment tests | BLOCKED at collection: Windows has no fcntl |
| Generated output/ignore | PASS for Online, V1, seven suites and TS caches; git check-ignore confirms all .build targets, including prospective Public site |
| Static consumer consistency and diff whitespace | PASS |

Public review.md worktree SHA256 is f32a4a35eb19e453e0a74d322164877e72ee028941234c9f17571231f627e6d0;
baseline Git blob SHA256 is a63dcb2b7da1b404240a19dd8131679fb31a63fcef433aa047cc0a2076d154f5,
matching the registered digest. Difference is CRLF checkout only. All 16 mismatching reviewed
payloads likewise match baseline Git blob hashes and differ only by CRLF. No payload, digest,
review or safety assertion was modified to make these checks pass.
Python failing tests are test_existing_output_rejected (pytest temp root inside repository)
and test_dataset_audit_accepts_readonly_uri_and_rejects_other_roots (Windows URI handling).
Their implementation and tests are unchanged from baseline.

Local command logs are in ignored `.build/tests/verification/`; browser scripts also report
their OS-temp evidence roots. Generated pytest-native output was moved into that ignored
verification directory. Existing ignored dist, dist-demo, dist-demo-shell and six dist-*-test
directories remain untouched; no old build or user data was deleted.

WP1B scope is defined, but its full acceptance prerequisite is not satisfied while Vitest,
Public exact-byte checks, browser runtime and Python platform checks remain BLOCKED.
No WP1B work was started. No financial, HTTP or deployment semantics changed.


## WP1A-R cross-platform reconciliation - 2026-11-13

This section supersedes the preceding WP1A blocker/closure conclusion. Verification baseline
is `81d65bc5683de38b4615c631d20357ef8aeb5f13` plus the minimal WP1A-R patch committed with
this record. Worktree was clean before changes. No merge, PR, push, deployment or WP1B work.

### Fixes and exact-byte evidence

No root Git Attributes existed; Windows system Git config had `core.autocrlf=true`.
Sixteen inventoried payloads and review.md had CRLF checkout bytes but LF Git blobs.
Root `.gitattributes` now lists exactly the 22 reviewed inputs: 21 text files use `text eol=lf`,
one gzip archive uses `-text`. Rules cover the entire existing payload inventory and Public
review evidence, including currently unaffected inputs. No reviewed digest was recomputed.
No Result or evidence blob changed: the refreshed worktree bytes equal baseline Git blobs.
Each file was checked for equality or CRLF-only difference before refresh; no user edits existed
or were overwritten. Forced `core.autocrlf=true, core.eol=crlf` checkout-index of all 22 paths
also produced byte-identical baseline blobs. Cross-platform rules are documented in STRUCTURE.

Two existing Windows-only tooling defects surfaced after hash admission succeeded:
Git tracked-file comparison now converts filesystem path separators to Git's `/` convention;
receipt npm-version acquisition uses the running npm CLI through Node when invoked by npm,
avoiding direct execution of a Windows .cmd shim. Neither change relaxes validation.

Actual integrity probes: original Result admitted; adding a space to a Result JSON string
was rejected with Public Result digest mismatch. Appending text to review.md was rejected
with Review evidence digest mismatch, then original bytes restored. Linux integrity tests
also passed artifact mutation, extra-file, symlink, credential and private-content rejection.
Public browser acceptance passed corrupted embedded digest -> Static Error with no fallback.

### Executed platform matrix

Linux used a separate local clone under `/tmp/wp1ar-vVjA7q/repo`, based on the baseline SHA
with identical patched tooling/attributes. It has its own repository-root `.venv` created by
Poetry and root ui_web npm project installed via `npm ci`; no module-local Python environment.
No existing Linux checkout or user's dependencies were overwritten. Versions: Ubuntu 24.04,
Node 22.22.1, Vitest 5.0.3, Poetry 2.2.1, Python 3.13. Windows Node is 22.23.2.

| Check | Windows | Linux/WSL formal result |
| --- | --- | --- |
| Public Demo Build | PASS after fixes and npm ci | PASS |
| Public Safety | PASS | PASS |
| Review/Result integrity probes | PASS | PASS via admission/integrity tests and browser corruption check |
| contract:check | NOT RUN in this reconciliation; WP1A passed | PASS |
| Online build | NOT RUN in this reconciliation; WP1A passed | PASS |
| lint | PASS | PASS |
| V1 and seven static builds | NOT RUN in this reconciliation; WP1A passed | PASS, all eight |
| static compatibility | NOT RUN in this reconciliation; WP1A passed | PASS |
| Default npm run test | See Windows limitation below | PASS: 84 files, 610 tests, 250.64 seconds |
| Four-worker diagnostic full run | NOT RUN | PASS: same 84 files, 610 tests, 114.66 seconds |
| Python tooling/deployment | BLOCKED/Deferred, details below | PASS: 20 tests (17 tooling + 3 deployment), 4.28 seconds |
| Seven static Browser Suites + V1 | NOT RUN; Linux selected | PASS, all eight |
| Public seven-page Browser Suite | NOT RUN; Linux selected | PASS, including exact assets, copy/export, charts and corrupted digest rejection |
| Online and V1 Vite preview HTTP smoke | NOT RUN | PASS: both returned HTTP 200 and HTML from new output roots |
| Public artifact verification | PASS during build | PASS, separate verify_public_artifact invocation |
| Path/ignore/workflow audit | PASS, static inspection | PASS, actual output paths and git check-ignore |
| Actual deployment / hosted acceptance | NOT RUN | NOT RUN, explicitly excluded |

Linux browser launch initially BLOCKED on `libnspr4.so`. Re-running with existing local
shared libraries resolved it: `LD_LIBRARY_PATH=/home/hg101/pwlibs/root/usr/lib/x86_64-linux-gnu`.
Chromium 1248 was already installed in WSL. Browser suites then passed unchanged.
An initial Public browser retry failed EEXIST because a previous failed launch had created
browser-local; rebuilding its explicitly owned generated Public output created a fresh artifact,
then the full Public browser suite passed. No source, history or user data was deleted.

### Worker investigation and Windows limitations

Windows pre-existing node_modules had Vitest 5.0.1 despite the lockfile resolving 5.0.3.
`npm ci` aligned it with Linux, without changing package.json/package-lock.json. Test discovery
found all 84 files. Linux workers launched and executed normally; no memory/cgroup cap or
swap pressure was observed (32 GiB RAM, 12 logical CPUs; maxWorkers remains 1 in config).
The first Linux default attempt was interrupted while diagnosing RUN-only output, not reported
as a pass. A clean default rerun completed all 610 tests. The four-worker diagnostic reporter
logged every module start/end and passed all 84 modules. No timeout, assertion, isolation,
test discovery or dependency versions in the lockfile were changed.

Windows focused run after npm ci: 2 files/6 tests PASS; public_release.test.ts FAIL due to
EPERM creating a file symlink. This is an OS privilege limitation, not a hash/path regression;
the exact test passed on Linux. Full default Windows invocations produced RUN-only output
within the observed windows and were interrupted. A verbose module reporter subsequently
confirmed worker startup and actual test progress (18 modules completed before the diagnostic
was stopped); RUN-only output alone is not proof of worker deadlock. Native Windows full-run qualification remains Deferred to the formal Linux
baseline; no test was disabled to obtain closure.

Windows Python retry with external --basetemp was BLOCKED at setup by WinError 5 creating
that OS-temp directory (17 setup errors, no claimed test passes). Original WP1A failures remain
explained: repository-local pytest temp output violates private output isolation; Windows
file URI handling fails the dataset audit. Both original failing tests passed unchanged in
Linux using its normal external pytest temp root. fcntl-dependent deployment tests also passed
on Linux, without mocks, SKIP or XFAIL. Native Windows Python support remains Deferred.

### Paths and closure

Static inspection confirms all retained npm build/preview commands consume `.build` configs;
Online `.build/online`, Public `.build/demo/site`, V1 `.build/tests/v1`, seven suites
`.build/tests/<suite>`, TypeScript and configurable Vite caches `.build/cache`.
Explicit external delivery and temporary runtime roots retain their semantics; node_modules
remains at ui_web root. Actual Linux outputs and git check-ignore matched these paths.
Pages upload/download agrees with Public receipt/artifact consumers; upload-artifact retains
`include-hidden-files: true`, and upload-pages-artifact points to `.build/demo/site`.
Local BuildOutput defaults to `.build/online`; build and deployment remain separate actions.
Workflow triggers, permissions, Environment and release strategy were not modified in WP1A-R.
GitHub Actions upload itself is a static check, not a live execution claim.

Reproducible formal commands, from the Linux verification repository:

```sh
poetry install --no-interaction
(cd ui_web && npm ci && npm run contract:check && npm run build && npm run lint && npm run test)
poetry run pytest ui_web/scripts ui_web/deploy -q
# In ui_web: demo:build:public, demo:build, the seven test:<suite>-static commands,
# test:static-compatibility, test:public-safety, the eight browser npm commands.
LD_LIBRARY_PATH=/home/hg101/pwlibs/root/usr/lib/x86_64-linux-gnu node scripts/public_demo_browser.mjs
```

Browser npm commands: test:static-shell-browser, test:option-chain-static-browser,
test:premium-static-browser, test:catalog-static-browser, test:explorer-static-browser,
test:futures-basis-static-browser, test:backtesting-static-browser and test:demo-browser.
Set LD_LIBRARY_PATH for all browser commands in this WSL installation. Run Public build
before the Public browser suite to ensure a fresh generated browser-local evidence directory.

Logs: Linux `/tmp/wp1ar-vVjA7q/repo/ui_web/.build/tests/wp1ar/`; Windows ignored
`ui_web/.build/tests/verification/wp1ar-*`. Linux logs are also copied to the Windows ignored
verification directory for review. Original failed probes remain distinguishable from passing reruns.

Closure: WP1A may close on the fully passing Linux regression baseline. Native Windows
limitations are Deferred and do not block WP1B. WP1B is ready to start under a separate task;
no WP1B implementation was performed here.
