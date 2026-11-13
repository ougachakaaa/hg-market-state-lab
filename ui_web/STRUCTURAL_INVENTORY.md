# WP0 baseline inventory

Expands the [migration matrix](STRUCTURAL_MIGRATION.md). Paths are ui_web-relative.
Classification is a planned disposition, not work performed. Family gates in the matrix apply to every member.

## Tracked tooling, Demo and specialized harness files

| Baseline file | Disposition / target | WP |
| --- | --- | --- |
| `.oxlintrc.json` | KEEP | 1 |
| `AGENTS.md` | KEEP | 1 |
| `ARCHITECTURE.md` | KEEP | 1 |
| `DATE_AXIS_PRESENTATION.md` | KEEP | 1 |
| `FEATURES.md` | KEEP | 1 |
| `VISUALIZATION.md` | KEEP | 1 |
| `VISUALIZATION_V2.md` | KEEP | 1 |
| `WP2A_ACCEPTANCE.md` | KEEP | 1 |
| `application.md` | KEEP | 1 |
| `contracts.md` | KEEP | 1 |
| `data-copy-export.md` | KEEP | 1 |
| `deploy/README.md` | KEEP deploy/; update output consumer | 1 |
| `deploy/deploy.config.example.psd1` | KEEP deploy/; update output consumer | 1 |
| `deploy/deploy.ps1` | KEEP deploy/; update output consumer | 1 |
| `deploy/publish.py` | KEEP deploy/; update output consumer | 1 |
| `deploy/test_publish.py` | MOVE tests/deploy/ | 1 |
| `index.html` | KEEP | 1 |
| `package-lock.json` | KEEP | 1 |
| `package.json` | KEEP | 1 |
| `presentation-architecture.md` | KEEP | 1 |
| `scripts/auth_browser_smoke.mjs` | MOVE tests/browser/auth_browser_smoke.mjs | 1 |
| `scripts/backtesting_browser_acceptance.mjs` | MOVE tests/browser/backtesting_browser_acceptance.mjs | 1 |
| `scripts/backtesting_browser_app.py` | MOVE tests/fixtures/backtesting_browser_app.py | 1 |
| `scripts/backtesting_static_browser.mjs` | MOVE tests/browser/backtesting_static_browser.mjs | 1 |
| `scripts/backtesting_static_isolation.test.ts` | MOVE tests/isolation/backtesting_static_isolation.test.ts | 1 |
| `scripts/build_private_demo.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/build_public_demo.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/catalog_static_browser.mjs` | MOVE tests/browser/catalog_static_browser.mjs | 1 |
| `scripts/catalog_static_isolation.test.ts` | MOVE tests/isolation/catalog_static_isolation.test.ts | 1 |
| `scripts/check_pages_environment.mjs` | MOVE deploy/pages/ | 4 |
| `scripts/contract_types.mjs` | KEEP scripts/ | 1 |
| `scripts/daily_data_copy_export_browser.mjs` | MOVE tests/browser/daily_data_copy_export_browser.mjs | 1 |
| `scripts/explorer_static_browser.mjs` | MOVE tests/browser/explorer_static_browser.mjs | 1 |
| `scripts/explorer_static_isolation.test.ts` | MOVE tests/isolation/explorer_static_isolation.test.ts | 1 |
| `scripts/export_contracts.py` | KEEP scripts/ | 1 |
| `scripts/extract_v1_rollback.mjs` | RETIRE | 4 |
| `scripts/futures_basis_browser_app.py` | MOVE tests/fixtures/futures_basis_browser_app.py | 1 |
| `scripts/futures_basis_demo_browser.mjs` | RETIRE | 3 |
| `scripts/futures_basis_offline_fixture.py` | MOVE tests/fixtures/futures_basis_offline_fixture.py | 1 |
| `scripts/futures_basis_online_browser.mjs` | MOVE tests/browser/futures_basis_online_browser.mjs | 1 |
| `scripts/futures_basis_polish_acceptance.mjs` | MOVE tests/browser/futures_basis_polish_acceptance.mjs | 1 |
| `scripts/futures_basis_report_browser.mjs` | MOVE tests/browser/futures_basis_report_browser.mjs | 1 |
| `scripts/futures_basis_static_browser.mjs` | MOVE tests/browser/futures_basis_static_browser.mjs | 1 |
| `scripts/futures_basis_static_isolation.test.ts` | MOVE tests/isolation/futures_basis_static_isolation.test.ts | 1 |
| `scripts/historical_basis_acceptance.mjs` | MOVE tests/browser/historical_basis_acceptance.mjs | 1 |
| `scripts/neutral_dark_acceptance.mjs` | MOVE tests/browser/neutral_dark_acceptance.mjs | 1 |
| `scripts/option_chain_static_browser.mjs` | MOVE tests/browser/option_chain_static_browser.mjs | 1 |
| `scripts/option_chain_static_isolation.test.ts` | MOVE tests/isolation/option_chain_static_isolation.test.ts | 1 |
| `scripts/package_futures_basis_report.mjs` | KEEP scripts/ | 1 |
| `scripts/premium_static_browser.mjs` | MOVE tests/browser/premium_static_browser.mjs | 1 |
| `scripts/premium_static_isolation.test.ts` | MOVE tests/isolation/premium_static_isolation.test.ts | 1 |
| `scripts/private_demo_boundary.mjs` | MERGE demo/build/ explicit input isolation | 2-3 |
| `scripts/private_demo_browser.mjs` | MOVE tests/browser/private_demo_browser.mjs | 1 |
| `scripts/private_demo_isolation.mjs` | MERGE demo/build/ isolation/safety | 2-3 |
| `scripts/private_demo_isolation.test.ts` | MOVE tests/isolation/private_demo_isolation.test.ts | 1 |
| `scripts/private_demo_negative.mjs` | MOVE tests/browser/private_demo_negative.mjs | 1 |
| `scripts/private_demo_projection.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/private_mo_examples.py` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/private_wpa_examples.py` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/public_admission_status.mjs` | MOVE deploy/pages/ | 4 |
| `scripts/public_asset_safety.mjs` | MERGE demo/build/ isolation/safety | 2-3 |
| `scripts/public_asset_safety.test.ts` | MOVE tests/tooling/public_asset_safety.test.ts | 1 |
| `scripts/public_demo_browser.mjs` | SPLIT tests/browser/ assertions and deploy/pages/ online runner | 4 |
| `scripts/public_payload_inventory.json` | MERGE demo/build/ isolation/safety | 2-3 |
| `scripts/public_release.mjs` | SPLIT demo/build/ and deploy/pages/ | 4 |
| `scripts/public_release.test.ts` | MOVE tests/tooling/public_release.test.ts | 1 |
| `scripts/research_browser_acceptance.mjs` | MOVE tests/browser/research_browser_acceptance.mjs | 1 |
| `scripts/research_browser_fixture.py` | MOVE tests/fixtures/research_browser_fixture.py | 1 |
| `scripts/research_browser_smoke.mjs` | MOVE tests/browser/research_browser_smoke.mjs | 1 |
| `scripts/staticPresentationIsolation.ts` | MERGE demo/build/ isolation/safety | 2-3 |
| `scripts/static_compatibility.mjs` | MOVE tests/isolation/static_compatibility.mjs | 1 |
| `scripts/static_shell_browser.mjs` | MOVE tests/browser/static_shell_browser.mjs | 1 |
| `scripts/static_shell_isolation.test.ts` | MOVE tests/isolation/static_shell_isolation.test.ts | 1 |
| `scripts/test_export_contracts.py` | MOVE tests/tooling/test_export_contracts.py | 1 |
| `scripts/test_private_wpa_examples.py` | MOVE tests/tooling/test_private_wpa_examples.py | 1 |
| `scripts/validate_private_basis.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/validate_private_mo.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/validate_private_wpa.mjs` | MERGE demo/build/ (tests to tests/) | 2-3 |
| `scripts/verify_public_artifact.mjs` | MOVE deploy/pages/ | 4 |
| `scripts/verify_v1_online.mjs` | RETIRE | 4 |
| `scripts/verify_v1_rollback.mjs` | RETIRE | 4 |
| `scripts/visualization_browser_smoke.mjs` | MOVE tests/browser/visualization_browser_smoke.mjs | 1 |
| `scripts/wp8_acceptance_status.mjs` | MOVE tests/browser/wp8_acceptance_status.mjs | 1 |
| `scripts/wp8_acceptance_status.test.mjs` | MOVE tests/tooling/wp8_acceptance_status.test.mjs | 1 |
| `scripts/wp8_real_acceptance.mjs` | MOVE tests/browser/wp8_real_acceptance.mjs | 1 |
| `src/demo/ARCHITECTURE.md` | MOVE demo/ARCHITECTURE.md | 3 |
| `src/demo/AUTHENTICITY.md` | MOVE demo/AUTHENTICITY.md | 2 |
| `src/demo/D7_READINESS.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/D7_RELEASE_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/EXAMPLES.md` | MOVE demo/EXAMPLES.md | 2 |
| `src/demo/IMPLEMENTATION.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/INTEGRATION_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/PRIVATE_BUILD.md` | MERGE demo/build/ARCHITECTURE.md | 3 |
| `src/demo/PUBLIC_BUILD.md` | MERGE demo/build/ARCHITECTURE.md | 3 |
| `src/demo/R1_FEASIBILITY.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/R2_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/R3_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/RELEASE.md` | MOVE deploy/pages/ARCHITECTURE.md | 4 |
| `src/demo/WP_A_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/WP_B_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/WP_C_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/futures_basis/ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/futures_basis/ARCHITECTURE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/futures_basis/DEPLOYMENT_ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/futures_basis/README.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/futures_basis/demo.css` | RETIRE | 3 |
| `src/demo/futures_basis/fixture.test.ts` | RETIRE | 3 |
| `src/demo/futures_basis/fixture.ts` | RETIRE | 3 |
| `src/demo/futures_basis/index.html` | RETIRE | 3 |
| `src/demo/futures_basis/main.tsx` | RETIRE | 3 |
| `src/demo/futures_basis/report.v1.json` | RETIRE | 3 |
| `src/demo/futures_basis/rollback-inventory.json` | RETIRE | 4 |
| `src/demo/futures_basis/rollback-v1.tar.gz` | RETIRE | 4 |
| `src/demo/private/PrivateWorkspace.tsx` | MERGE demo/runtime/ | 3 |
| `src/demo/private/admission.test.ts` | MERGE tests/demo/admission.test.ts | 3 |
| `src/demo/private/admission.ts` | MERGE demo/runtime/ | 3 |
| `src/demo/private/index.html` | MERGE demo/runtime/ | 3 |
| `src/demo/private/main.tsx` | MERGE demo/runtime/ | 3 |
| `src/demo/private/virtual.d.ts` | MERGE demo/runtime/ | 3 |
| `src/demo/public/admission.test.ts` | MERGE tests/demo/admission.test.ts | 3 |
| `src/demo/public/admission.ts` | MERGE demo/runtime/ | 3 |
| `src/demo/public/examples/README.md` | MOVE demo/bundles/README.md; current packaging guidance | 2 |
| `src/demo/public/examples/evidence/review.md` | MOVE demo/bundles/evidence/review.md; separate evidence from Manifest/hash admission | 2 |
| `src/demo/public/examples/package.json` | MERGE demo/bundles/ | 2 |
| `src/demo/public/index.html` | MERGE demo/runtime/ | 3 |
| `src/demo/public/main.tsx` | MERGE demo/runtime/ | 3 |
| `src/demo/public/virtual.d.ts` | MERGE demo/runtime/ | 3 |
| `src/demo/shell/ACCEPTANCE.md` | RETIRE after extracting valid Authority; history remains in Git | 3 |
| `src/demo/shell/StaticShellHarness.tsx` | MOVE tests/static/shell/ | 1 |
| `src/demo/shell/hashRoutes.ts` | MERGE demo/runtime/ | 3 |
| `src/demo/shell/index.html` | MOVE tests/static/shell/ | 1 |
| `src/demo/shell/main.tsx` | MOVE tests/static/shell/ | 1 |
| `src/demo/static/StaticWorkspace.tsx` | MERGE demo/runtime/ | 3 |
| `src/demo/static/results.ts` | MERGE demo/runtime/ | 3 |
| `src/features/backtesting/testing/static/index.html` | MOVE tests/static/backtesting/ | 1 |
| `src/features/backtesting/testing/static/main.tsx` | MOVE tests/static/backtesting/ | 1 |
| `src/features/futures_basis_research/testing/static/index.html` | MOVE tests/static/futures_basis_research/ | 1 |
| `src/features/futures_basis_research/testing/static/main.tsx` | MOVE tests/static/futures_basis_research/ | 1 |
| `src/features/mo_option_chain/testing/static/index.html` | MOVE tests/static/mo_option_chain/ | 1 |
| `src/features/mo_option_chain/testing/static/main.tsx` | MOVE tests/static/mo_option_chain/ | 1 |
| `src/features/mo_option_premium/testing/static/index.html` | MOVE tests/static/mo_option_premium/ | 1 |
| `src/features/mo_option_premium/testing/static/main.tsx` | MOVE tests/static/mo_option_premium/ | 1 |
| `src/features/research_catalog/testing/static/index.html` | MOVE tests/static/research_catalog/ | 1 |
| `src/features/research_catalog/testing/static/main.tsx` | MOVE tests/static/research_catalog/ | 1 |
| `src/features/research_explorer/testing/static/index.html` | MOVE tests/static/research_explorer/ | 1 |
| `src/features/research_explorer/testing/static/main.tsx` | MOVE tests/static/research_explorer/ | 1 |
| `src/shared/visualization/FixtureHarness.tsx` | MOVE tests/visualization/ | 1 |
| `tsconfig.app.json` | KEEP root; update output/discovery | 1 |
| `tsconfig.backtesting.json` | MOVE tests/config/ | 1 |
| `tsconfig.catalog.json` | MOVE tests/config/ | 1 |
| `tsconfig.demo.json` | MERGE demo/build/ | 2-3 |
| `tsconfig.explorer.json` | MOVE tests/config/ | 1 |
| `tsconfig.futures-basis.json` | MOVE tests/config/ | 1 |
| `tsconfig.json` | KEEP root; update output/discovery | 1 |
| `tsconfig.node.json` | KEEP root; update output/discovery | 1 |
| `tsconfig.option-chain.json` | MOVE tests/config/ | 1 |
| `tsconfig.premium.json` | MOVE tests/config/ | 1 |
| `tsconfig.private.json` | MERGE demo/build/ | 2-3 |
| `tsconfig.public.json` | MERGE demo/build/ | 2-3 |
| `tsconfig.shell.json` | MOVE tests/config/ | 1 |
| `ui-system.md` | KEEP | 1 |
| `visualization-harness.html` | MOVE tests/visualization/ | 1 |
| `vite.backtesting.config.ts` | MOVE tests/config/ | 1 |
| `vite.catalog.config.ts` | MOVE tests/config/ | 1 |
| `vite.config.test.ts` | KEEP root; update output/discovery | 1 |
| `vite.config.ts` | KEEP root; update output/discovery | 1 |
| `vite.demo.config.ts` | MERGE demo/build/ | 2-3 |
| `vite.explorer.config.ts` | MOVE tests/config/ | 1 |
| `vite.futures-basis.config.ts` | MOVE tests/config/ | 1 |
| `vite.option-chain.config.ts` | MOVE tests/config/ | 1 |
| `vite.premium.config.ts` | MOVE tests/config/ | 1 |
| `vite.shell.config.ts` | MOVE tests/config/ | 1 |
| `workspace-work-packages.md` | KEEP | 1 |
| `workspace.md` | KEEP | 1 |

Other tracked src files KEEP their owner, including co-located unit tests, static Presentation hooks,
feature testing Authority and formal offline reader. Root Authority remains in place except explicit routing updates.

## Every baseline npm command

| npm script | Current command | Target ownership / gate |
| --- | --- | --- |
| `dev` | `vite` | KEEP root command; WP1 output/test discovery |
| `build` | `tsc -b && vite build` | KEEP root command; WP1 output/test discovery |
| `contract:generate` | `poetry --directory .. run python ui_web/scripts/export_contracts.py && node scripts/contract_types.mjs` | KEEP general contract tooling; WP1 test paths |
| `contract:check` | `poetry --directory .. run python ui_web/scripts/export_contracts.py --check && node scripts/contract_types.mjs --check` | KEEP general contract tooling; WP1 test paths |
| `lint` | `oxlint` | KEEP root command; WP1 output/test discovery |
| `test` | `vitest run` | KEEP root command; WP1 output/test discovery |
| `preview` | `vite preview` | KEEP root command; WP1 output/test discovery |
| `test:futures-basis-online-browser` | `node scripts/futures_basis_online_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:auth-browser` | `node scripts/auth_browser_smoke.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:research-browser` | `node scripts/research_browser_smoke.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:visualization-browser` | `node scripts/visualization_browser_smoke.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `report:futures-basis` | `node scripts/package_futures_basis_report.mjs` | KEEP general report tooling; WP1 generated output path |
| `test:futures-basis-report-browser` | `node scripts/futures_basis_report_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:daily-data-copy-export-browser` | `node scripts/daily_data_copy_export_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:backtesting-browser` | `node scripts/backtesting_browser_acceptance.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `demo:dev` | `vite --config vite.demo.config.ts` | WP2-3 sole demo/build; retire private/public aliases at cutover |
| `demo:build` | `tsc -p tsconfig.demo.json && vite build --config vite.demo.config.ts` | WP2-3 sole demo/build; retire private/public aliases at cutover |
| `demo:preview` | `vite preview --config vite.demo.config.ts` | WP2-3 sole demo/build; retire private/public aliases at cutover |
| `test:demo-browser` | `node scripts/futures_basis_demo_browser.mjs` | WP3 replace V1 with sole formal seven-route acceptance |
| `test:static-shell` | `tsc -p tsconfig.shell.json && vite build --config vite.shell.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:static-shell-browser` | `node scripts/static_shell_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:option-chain-static` | `tsc -p tsconfig.option-chain.json && vite build --config vite.option-chain.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:option-chain-static-browser` | `node scripts/option_chain_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:premium-static` | `tsc -p tsconfig.premium.json && vite build --config vite.premium.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:premium-static-browser` | `node scripts/premium_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:catalog-static` | `tsc -p tsconfig.catalog.json && vite build --config vite.catalog.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:catalog-static-browser` | `node scripts/catalog_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:explorer-static` | `tsc -p tsconfig.explorer.json && vite build --config vite.explorer.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:explorer-static-browser` | `node scripts/explorer_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:futures-basis-static` | `tsc -p tsconfig.futures-basis.json && vite build --config vite.futures-basis.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:futures-basis-static-browser` | `node scripts/futures_basis_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:backtesting-static` | `tsc -p tsconfig.backtesting.json && vite build --config vite.backtesting.config.ts` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:backtesting-static-browser` | `node scripts/backtesting_static_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `demo:build:private` | `tsc -p tsconfig.private.json && node scripts/build_private_demo.mjs` | WP2-3 sole demo/build; retire private/public aliases at cutover |
| `test:private-demo-browser` | `node scripts/private_demo_browser.mjs` | WP1 tests/ relocation; retain assertions and explicit command coverage |
| `test:private-demo-data` | `node scripts/private_demo_negative.mjs` | WP2-3 preserve/merge effective validation; replace V1/private identity assumptions |
| `test:static-compatibility` | `tsc -p tsconfig.private.json && tsc -p tsconfig.public.json && node scripts/static_compatibility.mjs` | WP2-3 preserve/merge effective validation; replace V1/private identity assumptions |
| `test:public-safety` | `node scripts/public_asset_safety.mjs` | WP2-3 preserve/merge effective validation; replace V1/private identity assumptions |
| `demo:build:public` | `tsc -p tsconfig.public.json && node scripts/build_public_demo.mjs` | WP2-3 sole demo/build; retire private/public aliases at cutover |
| `test:public-admission` | `vitest run src/demo/public/admission.test.ts scripts/public_release.test.ts` | WP2-3 preserve/merge effective validation; replace V1/private identity assumptions |

## Generated and external surfaces

| Surface | Disposition / evidence |
| --- | --- |
| Ignored local dist, dist-demo, dist-demo-shell, dist-backtesting-test, dist-catalog-test, dist-explorer-test, dist-futures-basis-test, dist-option-chain-test, dist-premium-test | Observed locally; no inspection of payload contents needed; WP4 cleanup after consumer switch |
| dist-demo-public, dist-ssr | Ignored configured outputs; local existence not assumed; target .build/ |
| node_modules/.tmp TS caches; static_compatibility OS temporary builds | WP1 .build/cache and .build/tests; dependencies remain node_modules |
| External private R2/R3/WPA and output roots | No discovery or deletion; preserve isolation, never auto-copy into public bundles |
| .github/workflows/{demo-compatibility,deploy-demo-pages,release-preflight}.yml | KEEP repository location; invocation chains and WP gates in migration audit |
| market_research/scripts/futures_basis_demo_fixture.py and tests/test_futures_basis_demo_fixture.py | WP4 producer-policy reconciliation before retirement; Python workflow check is active |

## WP1A current output override

Tables above preserve WP0 baseline observations. Current producers/consumers use `.build/online`,
`.build/demo`, `.build/tests/v1`, `.build/tests/{shell,option-chain,premium,catalog,explorer,futures-basis,backtesting}`
and `.build/cache`. Source/config/test relocation remains WP1B. npm commands retain names:
their configs/scripts own output defaults. Old ignored dist directories are retained.
Explicit external private/report delivery roots and browser temporary runtimes remain unchanged.
