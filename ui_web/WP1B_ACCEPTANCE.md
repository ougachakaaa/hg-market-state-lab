# WP1B execution evidence - 2026-11-13

Baseline: `5da36dbf000e41e8d0dbfbfd72d5308ceb1b88e1`; branch `chore/ui-web-structural-consolidation`.
No PR, merge, push or deployment. Two sequential commits preserve the WP1A output layout.

## Stage 1 relocation

Seven specialized Vite/TSConfig pairs and static/Visualization harnesses moved below.
Configuration inheritance remains unchanged; no new configuration framework. Production imports,
feature unit tests and runtime hash routing retain their owners. Root app type checking explicitly
includes relocated static and Visualization harnesses. Public Safety recognizes only the seven
relocated TSConfig names as configuration; credential and reviewed-payload checks remain intact.

| Previous path | Current path |
| --- | --- |
| `vite.shell.config.ts` | `tests/config/vite.shell.config.ts` |
| `tsconfig.shell.json` | `tests/config/tsconfig.shell.json` |
| `vite.option-chain.config.ts` | `tests/config/vite.option-chain.config.ts` |
| `tsconfig.option-chain.json` | `tests/config/tsconfig.option-chain.json` |
| `vite.premium.config.ts` | `tests/config/vite.premium.config.ts` |
| `tsconfig.premium.json` | `tests/config/tsconfig.premium.json` |
| `vite.catalog.config.ts` | `tests/config/vite.catalog.config.ts` |
| `tsconfig.catalog.json` | `tests/config/tsconfig.catalog.json` |
| `vite.explorer.config.ts` | `tests/config/vite.explorer.config.ts` |
| `tsconfig.explorer.json` | `tests/config/tsconfig.explorer.json` |
| `vite.futures-basis.config.ts` | `tests/config/vite.futures-basis.config.ts` |
| `tsconfig.futures-basis.json` | `tests/config/tsconfig.futures-basis.json` |
| `vite.backtesting.config.ts` | `tests/config/vite.backtesting.config.ts` |
| `tsconfig.backtesting.json` | `tests/config/tsconfig.backtesting.json` |
| `src/features/backtesting/testing/static/index.html` | `tests/static/backtesting/index.html` |
| `src/features/backtesting/testing/static/main.tsx` | `tests/static/backtesting/main.tsx` |
| `src/features/futures_basis_research/testing/static/index.html` | `tests/static/futures_basis_research/index.html` |
| `src/features/futures_basis_research/testing/static/main.tsx` | `tests/static/futures_basis_research/main.tsx` |
| `src/features/mo_option_chain/testing/static/index.html` | `tests/static/mo_option_chain/index.html` |
| `src/features/mo_option_chain/testing/static/main.tsx` | `tests/static/mo_option_chain/main.tsx` |
| `src/features/mo_option_premium/testing/static/index.html` | `tests/static/mo_option_premium/index.html` |
| `src/features/mo_option_premium/testing/static/main.tsx` | `tests/static/mo_option_premium/main.tsx` |
| `src/features/research_catalog/testing/static/index.html` | `tests/static/research_catalog/index.html` |
| `src/features/research_catalog/testing/static/main.tsx` | `tests/static/research_catalog/main.tsx` |
| `src/features/research_explorer/testing/static/index.html` | `tests/static/research_explorer/index.html` |
| `src/features/research_explorer/testing/static/main.tsx` | `tests/static/research_explorer/main.tsx` |
| `src/demo/shell/main.tsx` | `tests/static/shell/main.tsx` |
| `src/demo/shell/index.html` | `tests/static/shell/index.html` |
| `src/demo/shell/StaticShellHarness.tsx` | `tests/static/shell/StaticShellHarness.tsx` |
| `visualization-harness.html` | `tests/visualization/visualization-harness.html` |
| `src/shared/visualization/FixtureHarness.tsx` | `tests/visualization/FixtureHarness.tsx` |

## Verification environment

Formal verification uses WSL Ubuntu 24.04, isolated checkout `/tmp/wp1b-repo`, root Poetry
runtime and root ui_web npm dependencies. Browser commands use the existing Chromium 1248
and `LD_LIBRARY_PATH=/home/hg101/pwlibs/root/usr/lib/x86_64-linux-gnu`.
Logs: `.build/tests/wp1b-stage1/` in that checkout. An initial non-login shell lacked Poetry
on PATH; contract checking was rerun successfully from a login shell. This was a runner setup
error, not a skipped check. Native Windows qualification remains Deferred as in WP1A-R.

## Stage 1 results

PASS: contract:check, Online build, lint, default Vitest (84 files / 610 tests, 207.61s),
V1/Public builds, seven static builds, compatibility, Public Safety, seven static Browser
Suites and Visualization Browser. Online build module-graph probe excludes Demo/tests.
Initial six static builds correctly rejected the relocated HTML because the allowlist update
omitted index.html; corrected to exact suite main.tsx/index.html paths. All six builds and
all eight isolation test files were rerun successfully after correction. No assertion weakened.
Diff, relative import targets and whitespace reviewed before the first commit.

## Stage 2 relocation

First commit: `7034c87`. The following 41 paths moved without changing assertions.

| Previous path | Current path |
| --- | --- |
| `deploy/test_publish.py` | `tests/deploy/test_publish.py` |
| `scripts/auth_browser_smoke.mjs` | `tests/browser/auth_browser_smoke.mjs` |
| `scripts/backtesting_browser_acceptance.mjs` | `tests/browser/backtesting_browser_acceptance.mjs` |
| `scripts/backtesting_browser_app.py` | `tests/fixtures/backtesting_browser_app.py` |
| `scripts/backtesting_static_browser.mjs` | `tests/browser/backtesting_static_browser.mjs` |
| `scripts/backtesting_static_isolation.test.ts` | `tests/isolation/backtesting_static_isolation.test.ts` |
| `scripts/catalog_static_browser.mjs` | `tests/browser/catalog_static_browser.mjs` |
| `scripts/catalog_static_isolation.test.ts` | `tests/isolation/catalog_static_isolation.test.ts` |
| `scripts/daily_data_copy_export_browser.mjs` | `tests/browser/daily_data_copy_export_browser.mjs` |
| `scripts/explorer_static_browser.mjs` | `tests/browser/explorer_static_browser.mjs` |
| `scripts/explorer_static_isolation.test.ts` | `tests/isolation/explorer_static_isolation.test.ts` |
| `scripts/futures_basis_browser_app.py` | `tests/fixtures/futures_basis_browser_app.py` |
| `scripts/futures_basis_offline_fixture.py` | `tests/fixtures/futures_basis_offline_fixture.py` |
| `scripts/futures_basis_online_browser.mjs` | `tests/browser/futures_basis_online_browser.mjs` |
| `scripts/futures_basis_polish_acceptance.mjs` | `tests/browser/futures_basis_polish_acceptance.mjs` |
| `scripts/futures_basis_report_browser.mjs` | `tests/browser/futures_basis_report_browser.mjs` |
| `scripts/futures_basis_static_browser.mjs` | `tests/browser/futures_basis_static_browser.mjs` |
| `scripts/futures_basis_static_isolation.test.ts` | `tests/isolation/futures_basis_static_isolation.test.ts` |
| `scripts/historical_basis_acceptance.mjs` | `tests/browser/historical_basis_acceptance.mjs` |
| `scripts/neutral_dark_acceptance.mjs` | `tests/browser/neutral_dark_acceptance.mjs` |
| `scripts/option_chain_static_browser.mjs` | `tests/browser/option_chain_static_browser.mjs` |
| `scripts/option_chain_static_isolation.test.ts` | `tests/isolation/option_chain_static_isolation.test.ts` |
| `scripts/premium_static_browser.mjs` | `tests/browser/premium_static_browser.mjs` |
| `scripts/premium_static_isolation.test.ts` | `tests/isolation/premium_static_isolation.test.ts` |
| `scripts/private_demo_browser.mjs` | `tests/browser/private_demo_browser.mjs` |
| `scripts/private_demo_isolation.test.ts` | `tests/isolation/private_demo_isolation.test.ts` |
| `scripts/private_demo_negative.mjs` | `tests/browser/private_demo_negative.mjs` |
| `scripts/public_asset_safety.test.ts` | `tests/tooling/public_asset_safety.test.ts` |
| `scripts/public_release.test.ts` | `tests/tooling/public_release.test.ts` |
| `scripts/research_browser_acceptance.mjs` | `tests/browser/research_browser_acceptance.mjs` |
| `scripts/research_browser_fixture.py` | `tests/fixtures/research_browser_fixture.py` |
| `scripts/research_browser_smoke.mjs` | `tests/browser/research_browser_smoke.mjs` |
| `scripts/static_compatibility.mjs` | `tests/isolation/static_compatibility.mjs` |
| `scripts/static_shell_browser.mjs` | `tests/browser/static_shell_browser.mjs` |
| `scripts/static_shell_isolation.test.ts` | `tests/isolation/static_shell_isolation.test.ts` |
| `scripts/test_export_contracts.py` | `tests/tooling/test_export_contracts.py` |
| `scripts/test_private_wpa_examples.py` | `tests/tooling/test_private_wpa_examples.py` |
| `scripts/visualization_browser_smoke.mjs` | `tests/browser/visualization_browser_smoke.mjs` |
| `scripts/wp8_acceptance_status.mjs` | `tests/browser/wp8_acceptance_status.mjs` |
| `scripts/wp8_acceptance_status.test.mjs` | `tests/tooling/wp8_acceptance_status.test.mjs` |
| `scripts/wp8_real_acceptance.mjs` | `tests/browser/wp8_real_acceptance.mjs` |

## Commands and root structure

All 40 public npm script names remain. Only the following command values changed:

| npm name | Previous | Current |
| --- | --- | --- |
| `test:futures-basis-online-browser` | `node scripts/futures_basis_online_browser.mjs` | `node tests/browser/futures_basis_online_browser.mjs` |
| `test:auth-browser` | `node scripts/auth_browser_smoke.mjs` | `node tests/browser/auth_browser_smoke.mjs` |
| `test:research-browser` | `node scripts/research_browser_smoke.mjs` | `node tests/browser/research_browser_smoke.mjs` |
| `test:visualization-browser` | `node scripts/visualization_browser_smoke.mjs` | `node tests/browser/visualization_browser_smoke.mjs` |
| `test:futures-basis-report-browser` | `node scripts/futures_basis_report_browser.mjs` | `node tests/browser/futures_basis_report_browser.mjs` |
| `test:daily-data-copy-export-browser` | `node scripts/daily_data_copy_export_browser.mjs` | `node tests/browser/daily_data_copy_export_browser.mjs` |
| `test:backtesting-browser` | `node scripts/backtesting_browser_acceptance.mjs` | `node tests/browser/backtesting_browser_acceptance.mjs` |
| `test:static-shell` | `tsc -p tsconfig.shell.json && vite build --config vite.shell.config.ts` | `tsc -p tests/config/tsconfig.shell.json && vite build --config tests/config/vite.shell.config.ts` |
| `test:static-shell-browser` | `node scripts/static_shell_browser.mjs` | `node tests/browser/static_shell_browser.mjs` |
| `test:option-chain-static` | `tsc -p tsconfig.option-chain.json && vite build --config vite.option-chain.config.ts` | `tsc -p tests/config/tsconfig.option-chain.json && vite build --config tests/config/vite.option-chain.config.ts` |
| `test:option-chain-static-browser` | `node scripts/option_chain_static_browser.mjs` | `node tests/browser/option_chain_static_browser.mjs` |
| `test:premium-static` | `tsc -p tsconfig.premium.json && vite build --config vite.premium.config.ts` | `tsc -p tests/config/tsconfig.premium.json && vite build --config tests/config/vite.premium.config.ts` |
| `test:premium-static-browser` | `node scripts/premium_static_browser.mjs` | `node tests/browser/premium_static_browser.mjs` |
| `test:catalog-static` | `tsc -p tsconfig.catalog.json && vite build --config vite.catalog.config.ts` | `tsc -p tests/config/tsconfig.catalog.json && vite build --config tests/config/vite.catalog.config.ts` |
| `test:catalog-static-browser` | `node scripts/catalog_static_browser.mjs` | `node tests/browser/catalog_static_browser.mjs` |
| `test:explorer-static` | `tsc -p tsconfig.explorer.json && vite build --config vite.explorer.config.ts` | `tsc -p tests/config/tsconfig.explorer.json && vite build --config tests/config/vite.explorer.config.ts` |
| `test:explorer-static-browser` | `node scripts/explorer_static_browser.mjs` | `node tests/browser/explorer_static_browser.mjs` |
| `test:futures-basis-static` | `tsc -p tsconfig.futures-basis.json && vite build --config vite.futures-basis.config.ts` | `tsc -p tests/config/tsconfig.futures-basis.json && vite build --config tests/config/vite.futures-basis.config.ts` |
| `test:futures-basis-static-browser` | `node scripts/futures_basis_static_browser.mjs` | `node tests/browser/futures_basis_static_browser.mjs` |
| `test:backtesting-static` | `tsc -p tsconfig.backtesting.json && vite build --config vite.backtesting.config.ts` | `tsc -p tests/config/tsconfig.backtesting.json && vite build --config tests/config/vite.backtesting.config.ts` |
| `test:backtesting-static-browser` | `node scripts/backtesting_static_browser.mjs` | `node tests/browser/backtesting_static_browser.mjs` |
| `test:private-demo-browser` | `node scripts/private_demo_browser.mjs` | `node tests/browser/private_demo_browser.mjs` |
| `test:private-demo-data` | `node scripts/private_demo_negative.mjs` | `node tests/browser/private_demo_negative.mjs` |
| `test:static-compatibility` | `tsc -p tsconfig.private.json && tsc -p tsconfig.public.json && node scripts/static_compatibility.mjs` | `tsc -p tsconfig.private.json && tsc -p tsconfig.public.json && node tests/isolation/static_compatibility.mjs` |
| `test:public-admission` | `vitest run src/demo/public/admission.test.ts scripts/public_release.test.ts` | `vitest run src/demo/public/admission.test.ts tests/tooling/public_release.test.ts` |

CI matrix replaces `ui_web/scripts` with two explicit collection locations:
`ui_web/tests/tooling`, `ui_web/tests/deploy`. Other suites, frontend checks, triggers,
permissions, Environment and deployment definitions are unchanged. DEVELOPMENT.md follows
those test locations; Python lint includes scripts and tests.

| Tracked surface | Before | After |
| --- | --- | --- |
| Root Vite configs | 9 | 2 (Online and V1 Demo) |
| Root TSConfigs | 13 | 6 (root/app/node/demo/private/public) |
| scripts/ files | 65 | 25 |
| tests/config | 0 | 15 (14 moved + 1 Browser startup config) |
| tests/static | 0 | 15 |
| tests/visualization | 0 | 2 |
| tests/browser | 0 | 22 |
| tests/isolation | 0 | 9 |
| tests/fixtures | 0 | 4 |
| tests/tooling | 0 | 5 |
| tests/deploy | 0 | 1 |

No source files merged or tests deleted. Visualization evidence defaults to
`.build/tests/visualization-browser` instead of the previous node_modules-local evidence directory;
its explicit evidence override remains. No old dist directory or user data was deleted.
Dependencies remain at ui_web/node_modules. V1/private/public TS and V1 Vite configurations,
Demo build/runtime/safety implementations, Public/V1 runners and release tooling remain because
the migration matrix assigns them to WP2-WP4. Shared build isolation remains production-consumed.
Opt-in Private browser/data gates require external reviewed inputs; WP8 real acceptance requires
real-market input and visible Windows Chrome. These are not executed with fabricated inputs.
Their imports, source-root bases and parameter contracts are preserved.

## Stage 2 formal results

| Check | Linux result |
| --- | --- |
| contract:check / Online build / lint | PASS |
| Default Vitest | PASS: 84 files / 610 tests, 211.38s |
| Per-file coverage comparison | PASS: all 84 file counts identical to stage 1 after path mapping |
| Python tooling / deploy | PASS: 17 + 3 = 20, combined and separate CI collection |
| Python lint (scripts and tests) | PASS |
| V1 / Public build | PASS |
| Seven static builds | PASS through each relocated browser command's mandatory build |
| Static compatibility and eight isolation test files | PASS |
| Public Safety / public-admission integrity negatives | PASS |
| Seven specialized Browser Suites + V1 | PASS, all eight |
| Public seven-page Browser Suite | PASS, including corrupted-digest rejection |
| Visualization / offline report Browser | PASS |
| Artifact verification | PASS |
| Online loaded-module graph | PASS: no src/demo or tests module |
| Output path/ignore audit | PASS: ten entries under .build, no root dist* in fresh checkout |
| Browser runner syntax | PASS |

Stage 2 logs: `/tmp/wp1b-repo/ui_web/.build/tests/wp1b-stage2/`.
No count changes, SKIP/XFAIL, worker/timeout relaxations or assertion deletions.
Initial extended Online browser diagnostics failed: Auth title wait timeout; Research response-body
navigation race; Futures Basis route.fetch received 401; subsequent Backtesting and Copy/Export
startup encountered port 8011 still occupied. These are retained as initial failures, not passes.
A separate clean baseline checkout at `/tmp/wp1b-baseline`, exactly `5da36db`, passed all five
original extended Online commands. Validation cleans up only uvicorn/Vite processes whose cwd
belongs to these two task-owned checkouts, between suites; production sources are unchanged.
Final clean migrated reruns are recorded separately with `-retry.log` suffixes.

## Browser startup reconciliation and acceptance scope

A fresh checkout with its own Poetry environment and `npm ci` reproduced extended Online
browser failures. Logs showed Vite's implicit HTML dependency scan resolving Demo
`virtual:public-examples` / `virtual:private-examples` without Demo plugins, abandoning eager
optimization and later reloading the page during browser assertions. The structural cutover
must give browser startup an explicit entry rather than depend on implicit HTML discovery.

Added `tests/config/vite.browser.config.ts`: a small merge of existing Online settings with
`optimizeDeps.entries` fixed to the Online index. Five Online/opt-in browser launchers use it;
the Copy/Export harness's existing generated port/proxy config declares the same entry.
Root Online Vite configuration, application code, authentication, selectors, assertions,
timeouts and workers are unchanged. Root node TSConfig checks the new test configuration.
Final Online build and lint passed after this addition. This is one added config, not a
configuration-generation framework. Final Online browser logs use `-scoped.log` below
`/tmp/wp1b-clean/ui_web/.build/tests/wp1b-clean/`.

User scope update during execution: complete Demo builds are no longer a WP1B closure
prerequisite because Demo will change next. Existing Demo results above remain recorded;
no Demo repair or redesign is introduced, and no CI checks are removed by this local waiver.

Final scoped startup runs passed Auth, Research and Copy/Export. Futures Basis and Backtesting
had additional failures (Futures Basis authenticated run GET unexpectedly returned 401;
Backtesting timed out waiting for its expected missing-result presentation). A second unmodified
baseline run passed Futures Basis but failed Backtesting at line 314 with `401 !== 202`.
This establishes baseline Backtesting instability; it does not justify claiming every current
failure is harmless. Final bounded reruns of those two commands are logged as `-final.log`.
No business/HTTP/authentication implementation was modified to address these failures.

## Final status and remaining gates

| Extended Online Browser command | Final scoped result |
| --- | --- |
| test:auth-browser | PASS |
| test:research-browser | PASS |
| test:daily-data-copy-export-browser | PASS |
| test:futures-basis-online-browser | FAIL: final run timed out waiting for section-5 after an authenticated workflow; earlier unmodified runs also passed |
| test:backtesting-browser | FAIL: final presentation wait timed out; unmodified baseline also reproduced an unexpected 401 on repeat |

The final two commands were each rerun once after scoped startup, without assertion changes;
those failures remain open. Baseline Backtesting instability is established, but equivalence of
all remaining Online browser failures has not been established. No claim of a fully green
extended Online matrix or absence of every regression is made.

Implementation: all 72 planned moves and one small startup config addition are complete.
The full Vitest and Python counts are preserved, and the seven specialized + V1 and Public
seven-page gates passed. Root structure, changed commands and every moved path are listed above.
Final diff, import targets, npm-name identity and whitespace were reviewed before commit 2.

WP1B acceptance remains OPEN because two affected Online browser gates have not closed.
The user-waived complete Demo-build prerequisite is not the blocker. WP2's directory prerequisites
are in place, but WP1B does not yet provide an unconditional acceptance handoff to WP2. Stop here:
no Demo Bundle/runtime redesign, historical Demo deletion, business/HTTP/authentication change,
PR, merge, push or deployment was performed.

Logs (including first failures, successful retries, baseline and final failures) were copied to
ignored `ui_web/.build/tests/verification/wp1b/` in the Windows workspace. WSL source logs remain
under the three task-owned checkout roots documented above. No old dist outputs or user data
were deleted. Windows native Symlink/pytest/worker qualification remains Deferred as in WP1A-R.
