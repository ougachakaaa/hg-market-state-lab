# WP1B execution evidence ? 2026-11-13

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
