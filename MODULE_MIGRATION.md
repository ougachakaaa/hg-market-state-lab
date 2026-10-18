# Repository Directory and Namespace Migration Record

Engineering status as of 2026-10-18 (Asia/Shanghai), not a business authority. Canonical identities, runtime and dependency direction remain in [repository architecture](ARCHITECTURE.md#naming-and-transition-authority). Branch: `chore/module-namespace-migration`, based on `develop` commit `a71b5f9b7316007bf7f45297f4f01ee2e2e8255c`. The earlier authority-only handoff used reference `f2f66644e9ef04d7e9b83e2a177b5f718badc462`.

## Implemented layout

| Historical directory | Canonical directory | Python namespace change |
| --- | --- | --- |
| `data-lake/` | `data_lake/` | `data_lake` unchanged |
| `market-snapshot/` | `data_snapshot/` | `market_snapshot` → `data_snapshot` |
| `market-research/` | `market_research/` | `market_research` unchanged |
| `market-modeling/` | `market_modeling/` | Existing placeholder only; no package created |
| `lab/` | `ui_cli/` | `lab` → `ui_cli`; executable stays `lab` |
| `backend-api/` | `ui_http/` | `backend_api` → `ui_http` |
| `web-ui/` | `ui_web/` | npm project; no Python namespace |

Internal Provider / Dataset / Product / Observation / Component / Study / feature co-location is preserved. `data_lake/experiments/` has only a minimal [entry](data_lake/experiments/README.md); [Experiments authority](data_lake/EXPERIMENTS.md) governs isolation. It is excluded from formal package registration and consumer imports. Modeling still has no internal design or implementation.

Root Poetry registration, pytest/Ruff/mypy roots, CLI delegation, Research discovery/output configuration, HTTP launcher and consumers, frontend contract tooling, bootstrap, ignore rules, `.worktreeinclude`, authority navigation and operational examples use canonical paths. Test helpers use distinct `snapshot_support` / `http_support` names so root type checking resolves the correct fixtures; owning test directories are explicit mypy search roots. No business facade was redesigned and no compatibility package remains.

Distribution `hg-market-state-lab`, executable `lab`, npm package identity, Product/Dataset IDs, URLs, DTOs and public semantic request/result/failure contracts are unchanged. `poetry.lock`, npm lock contents and generated OpenAPI/TypeScript contents are unchanged. The HTTP runtime's published historical description is retained verbatim. Historical commands in [V1 acceptance evidence](data_lake/RELEASE_ACCEPTANCE.md) remain historical evidence, not current operational entries.

## Local runtime state

All seven implementation-checkout directories were renamed as complete directories, preserving ignored contents. A private temporary manifest verified all **262 pre-existing runtime/credential asset files** byte-for-byte with SHA-256 after the move. No credentials, SQLite files, Raw artifacts or outputs enter the implementation commit. Tests use fake Sources / temporary databases; no real Source acquisition or user-cache rebuild was used.

[Local migration guide](LOCAL_MIGRATION.md) defines storage locations and explicit copy/verify steps for other upgraded checkouts. `.codex/scripts/migrate_local_state.py` defaults to read-only inspection, refuses conflicting destinations and symlinks, copies exclusively with `--apply`, verifies hashes and never deletes source assets. Operators retain external backups and archive legacy sources explicitly after verification. Bootstrap, Dataset storage resolution, Snapshot Source/artifact access, Observation storage and Research output configuration reject applicable legacy state rather than silently adopting empty canonical storage. Isolated legacy DataLake caches remain isolated; no schema migration or rebuild is implied.

The existing root `.venv` was reused and root installation refreshed. Ignored module-local environments were retained as inactive historical files. Frontend dependencies belong to `ui_web/node_modules`; other worktrees install their own dependencies. No user installation directory was deleted for this migration.

## Executed verification

| Check | Result |
| --- | --- |
| Root `poetry install --no-interaction` | Passed; no dependency/version changes |
| Root `poetry run pytest -q -rs` | **1424 passed, 2 skipped**, 50.73 seconds |
| Repository Ruff and root mypy | Passed; mypy checked 188 source files; migration helper also checked separately |
| CLI doctor, datalake list, research list and Study `--help` | Passed; root Python 3.13.11, Node 22.23.2, npm 11.0.0 |
| External temporary cwd with installed `python -I` imports | 20 owning packages/services passed; retired `lab`, `market_snapshot`, `backend_api` imports absent; installed console entry `ui_cli.cli:main` |
| HTTP launcher from external cwd | Started on temporary loopback port, served unchanged `/mo-option-chain` and `/mo-option-premium-plane` OpenAPI routes, then stopped |
| HTTP route/DTO/OpenAPI; four Dataset Kernel/Provider/Service/SQLite; all Snapshot Product and Research boundary/runtime tests | Included in full pytest result |
| Frontend `npm install --ignore-scripts` | Passed; lock contents unchanged |
| Frontend `contract:generate` and `contract:check` | Passed; both OpenAPI and generated TypeScript contents unchanged |
| Frontend test, build, lint | Passed: 15 test files / 66 tests; production build completed |
| Authority links and heading anchors | 123 Markdown files, no findings; topology/reachability tests passed |
| Bootstrap syntax | Git Bash `bash -n` and PowerShell parser passed |
| Runtime safety | Controlled tests cover copy/idempotence/conflicts, SQLite companions and legacy-state rejection |
| Relocation/reference/diff audit | Every original tracked file accounted for; production changes beyond mechanical migration are local-state safeguards and preserved wire text; `git diff --check` passed |

## Limits and merge assessment

Two existing symlink tests remain **skipped**, not passed: CLI Research package discovery and Research output-layout symlink rejection. Windows returned WinError 1314 (no symlink-creation privilege). Ordinary discovery/output and boundary tests passed. Linux/WSL bootstrap execution was not exercised on this Windows host; both scripts passed syntax checks and Windows root install/readiness/launcher steps were exercised. No Linux runtime acceptance is claimed.

The unchanged frontend graph reports one existing npm audit high-severity transitive `source-map-js` finding. Dependency upgrades are outside this migration's explicit version-preservation constraint; no automatic audit fix was applied. Vite reports a large production-chunk warning; pytest reports a third-party Starlette/httpx deprecation warning. Neither warning indicates a namespace/path failure.

No structural migration work remains deferred. Implementation is ready for review and merge into `develop` within the verified Windows scope, with skipped platform scenarios, unexecuted Linux bootstrap and the unchanged dependency finding disclosed above. This record does not merge, publish or deploy the branch; target-branch changes still require normal review/CI.
