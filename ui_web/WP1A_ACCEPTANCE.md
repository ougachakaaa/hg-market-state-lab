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
