> Verification policy update, 2026-11-14: this record preserves its original results.
> Its cleanup/platform limitations do not block ordinary development or DDB-01.
> Follow the [current scoped policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).

# DDB-00 hard retirement — 2026-11-14

Legacy Synthetic V1 and Public/Private V2 Packages are retired by direct cutover.
No migration, fallback, rollback, archive or compatibility reader remains.
The new sole Demo Bundle Pipeline is NOT implemented. Demo build and publication
are BLOCKED and must fail. New business Results must be acquired through formal
FastAPI HTTP with normal authentication; direct producer/projection calls are forbidden.
Only one active dataset will be permitted. Existing shared Presentation, hash routing,
static composition and formal Result validators remain implementation foundations,
not a runnable historical Demo. Online Web and business contracts are unchanged.
Git history retains previous decisions; retired acceptance is not current readiness.

## Actual deleted tracked files

- `market_research/scripts/futures_basis_demo_fixture.py`
- `market_research/tests/test_futures_basis_demo_fixture.py`
- `ui_web/scripts/build_private_demo.mjs`
- `ui_web/scripts/build_public_demo.mjs`
- `ui_web/scripts/extract_v1_rollback.mjs`
- `ui_web/scripts/futures_basis_demo_browser.mjs`
- `ui_web/scripts/private_demo_boundary.mjs`
- `ui_web/scripts/private_demo_isolation.mjs`
- `ui_web/scripts/private_demo_projection.mjs`
- `ui_web/scripts/private_mo_examples.py`
- `ui_web/scripts/private_wpa_examples.py`
- `ui_web/scripts/public_admission_status.mjs`
- `ui_web/scripts/public_demo_browser.mjs`
- `ui_web/scripts/public_release.mjs`
- `ui_web/scripts/validate_private_basis.mjs`
- `ui_web/scripts/validate_private_mo.mjs`
- `ui_web/scripts/validate_private_wpa.mjs`
- `ui_web/scripts/verify_public_artifact.mjs`
- `ui_web/scripts/verify_v1_online.mjs`
- `ui_web/scripts/verify_v1_rollback.mjs`
- `ui_web/src/demo/AUTHENTICITY.md`
- `ui_web/src/demo/D7_READINESS.md`
- `ui_web/src/demo/D7_RELEASE_ACCEPTANCE.md`
- `ui_web/src/demo/EXAMPLES.md`
- `ui_web/src/demo/IMPLEMENTATION.md`
- `ui_web/src/demo/INTEGRATION_ACCEPTANCE.md`
- `ui_web/src/demo/PRIVATE_BUILD.md`
- `ui_web/src/demo/PUBLIC_BUILD.md`
- `ui_web/src/demo/R1_FEASIBILITY.md`
- `ui_web/src/demo/R2_ACCEPTANCE.md`
- `ui_web/src/demo/R3_ACCEPTANCE.md`
- `ui_web/src/demo/RELEASE.md`
- `ui_web/src/demo/WP_A_ACCEPTANCE.md`
- `ui_web/src/demo/WP_B_ACCEPTANCE.md`
- `ui_web/src/demo/WP_C_ACCEPTANCE.md`
- `ui_web/src/demo/futures_basis/ACCEPTANCE.md`
- `ui_web/src/demo/futures_basis/ARCHITECTURE.md`
- `ui_web/src/demo/futures_basis/DEPLOYMENT_ACCEPTANCE.md`
- `ui_web/src/demo/futures_basis/README.md`
- `ui_web/src/demo/futures_basis/demo.css`
- `ui_web/src/demo/futures_basis/fixture.test.ts`
- `ui_web/src/demo/futures_basis/fixture.ts`
- `ui_web/src/demo/futures_basis/index.html`
- `ui_web/src/demo/futures_basis/main.tsx`
- `ui_web/src/demo/futures_basis/report.v1.json`
- `ui_web/src/demo/futures_basis/rollback-inventory.json`
- `ui_web/src/demo/futures_basis/rollback-v1.tar.gz`
- `ui_web/src/demo/private/PrivateWorkspace.tsx`
- `ui_web/src/demo/private/admission.test.ts`
- `ui_web/src/demo/private/admission.ts`
- `ui_web/src/demo/private/index.html`
- `ui_web/src/demo/private/main.tsx`
- `ui_web/src/demo/private/virtual.d.ts`
- `ui_web/src/demo/public/admission.test.ts`
- `ui_web/src/demo/public/admission.ts`
- `ui_web/src/demo/public/examples/README.md`
- `ui_web/src/demo/public/examples/evidence/review.md`
- `ui_web/src/demo/public/examples/package.json`
- `ui_web/src/demo/public/index.html`
- `ui_web/src/demo/public/main.tsx`
- `ui_web/src/demo/public/virtual.d.ts`
- `ui_web/tests/browser/private_demo_browser.mjs`
- `ui_web/tests/browser/private_demo_negative.mjs`
- `ui_web/tests/isolation/static_compatibility.mjs`
- `ui_web/tests/tooling/test_private_wpa_examples.py`
- `ui_web/tsconfig.demo.json`
- `ui_web/tsconfig.private.json`
- `ui_web/tsconfig.public.json`
- `ui_web/vite.demo.config.ts`

## Scope, retained implementation and test retirement

Baseline: clean develop at b31835dbbf09d7d6c9265a9fd28497fd430cc345;
created feat/demo-bundle-workflow from that exact commit. No merge or remote mutation.

Retained: Online src/app and every feature business implementation; all generated
OpenAPI/TypeScript; formal Result validators; shared React Presentation and charts;
StaticWorkspace and composition-only types; hashRoutes; seven independent static
harnesses; transport-free feature controllers; source credential and reviewed-payload
scan; exact-byte artifact integrity, extra-file and symlink rejection; static import
security checks; Pages environment inspection. Backend, DataLake and Research data
and independent Python/TS business fixtures were not deleted.

Deleted tests: V1 fixture/regeneration tests prove only the removed Demo generator;
private/public admission tests, private browser/negative tests and private WPA tooling
tests exercise removed Envelope/generation APIs. Combined legacy entry graph runner
is removed; specialized static graph rejection tests remain. V1-only safety assertion
and V1 date exclusion are removed. Generic credential/artifact/isolation tests remain.
Independent Futures Basis tests now construct fresh inputs from reader.fixture.ts;
no legacy JSON was copied. Fixed request/coverage expectations follow those new facts.
Old Demo-driven browser chart/metric/slot assertions retired with that dataset;
independent reader/Visualization/Presentation unit tests remain. Browser routing,
static isolation, invalid payload rejection and no-network assertions remain.

CI/npm: removed all V1/private/public build, dev, preview, browser and admission aliases.
Only demo:build remains, exits 1 with BLOCKED. Compatibility runs core/source safety
before failing this build. Pages has no artifact upload/deploy/recovery action;
publication cannot PASS. release-preflight.yml and remote settings are untouched.
Static configs inherit the Online TS options and a test-owned static Vite base.
Authority: Demo ARCHITECTURE, STRUCTURE, STRUCTURAL_MIGRATION, STRUCTURAL_INVENTORY,
module/presentation navigation, linked feature contracts and README are reconciled;
obsolete Demo authorities and acceptance entry points are deleted, retained evidence
links identify retirement. Git history is unchanged.

## Verification and limitations

- Online build, contract:check, lint, source safety: PASS.
- demo:build: expected exit 1 / BLOCKED (no Bundle Pipeline).
- Futures Basis static browser with installed Edge: PASS, zero Auth/API requests.
- Targeted formal validator/coverage/isolation/tooling: 24 passed; generic artifact
  test initially ENVIRONMENT_BLOCKED by Windows file-symlink permission, then PASS
  using an actual directory junction. Final Presentation/artifact/retirement: 6 PASS.
- Python initial combined regression: 1305 passed, 3 skipped, 4 failed. Three failures
  require outside-repository temp roots (HARNESS_FAILURE); one broken authority-link
  regression was fixed, authority topology then 13 PASS. One clean external-temp rerun
  was ENVIRONMENT_BLOCKED by WinError 5, not counted as passing.
- Python deployment test collection: ENVIRONMENT_BLOCKED (Windows lacks fcntl).
- ruff market_research and mypy market_research/tests: PASS.
- Full frontend run results are recorded below after completion.
- New Bundle build/publication/browser acceptance: BLOCKED, not implemented.

## Local cleanup blocked by policy

Automatic approval review rejected the verified recursive cleanup command with
`blocked by policy`. No bypass was attempted. The old ignored output directories
below and task helper files therefore remain; they are not current build inputs.
Acceptance 1 is NOT unconditionally PASS for the entire physical workspace.
Run the exact commands in DDB_00_CLEANUP.ps1 from repository root after review.
It removes only identified generated Demo/test outputs and this task's helpers;
no tracked source, formal evidence, credentials or external/raw/cache data.

DDB-01 design/implementation can start from the retired tracked tree, but this is
not unconditional DDB-00 acceptance: local cleanup and listed verification blockers
remain. No DDB-01 work was performed. main/develop refs remain unchanged; no push,
Pages deployment or remote configuration operation was issued.

Seven specialized static builds: shell, option-chain, premium, catalog, explorer,
futures-basis, backtesting all PASS. Final Online rebuild/lint/source-safety PASS.
The first frontend run overlapped implementation corrections (18 failures); second
full run was 592 PASS / 2 FAIL (pre-fix symlink test and fixed-request dates in static
hook test). Both causes have been corrected without changing production behavior;
final complete rerun follows. Retained evidence reports never treat these as PASS.

## Final frontend result

Final complete `npm test -- --reporter=dot`: **82 files / 595 tests PASS**
(exit 0, 321.98 seconds). All retained business tests pass. Online build,
contract:check, lint and source safety PASS; all seven static builds PASS;
Futures Basis static browser PASS. No new Pipeline/publication test is claimed PASS.

DDB-01 handoff decision: **not unconditional**. The tracked implementation is ready
for new Pipeline work, but full physical-worktree retirement acceptance is BLOCKED
until the user executes the provided exact cleanup commands. Python platform/temp
limitations remain separately recorded. Stop here; do not implement DDB-01.
