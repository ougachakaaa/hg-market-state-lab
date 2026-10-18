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

## Disposable runtime state reconciliation

The final cleanup is based on `904f0e9d93b878e8202b01eb69d9e21fc934ef65`. The [repository authority](ARCHITECTURE.md#naming-and-transition-authority) now explicitly treats all local running data as disposable. Canonical Dataset caches, Snapshot Raw / outputs, Observation SQLite and Research outputs are used directly, regardless of historical directories. Local data has no cross-directory migration or compatibility obligation.

The local-state migration helper, dedicated migration tests, bootstrap preflight, runtime legacy-directory guards and historical-directory ignore rules have been removed. No user data or historical local directory is deleted. Credentials are configured through the current environment or canonical `.env`; historical tokens are not migrated. Root Poetry and frontend worktree-local dependency ownership remain unchanged.

Dataset generation 3 / rebuild-only compatibility, schema and content integrity, read-only behavior, Observation complete lookup / atomic durable publication, and Study output collision / overwrite / staging semantics remain unchanged. Retained business semantics inside canonical storage do not imply filesystem migration obligations. The local migration guide and its operational instructions have been retired.

## Baseline verification at `904f0e9`

| Check | Result |
| --- | --- |
| Root `poetry install --no-interaction` | Passed; no dependency/version changes |
| Root `poetry run pytest -q -rs` | **1424 passed, 2 skipped**, 50.73 seconds |
| Repository Ruff and root mypy | Passed; mypy checked 188 source files |
| CLI doctor, datalake list, research list and Study `--help` | Passed; root Python 3.13.11, Node 22.23.2, npm 11.0.0 |
| External temporary cwd with installed `python -I` imports | 20 owning packages/services passed; retired `lab`, `market_snapshot`, `backend_api` imports absent; installed console entry `ui_cli.cli:main` |
| HTTP launcher from external cwd | Started on temporary loopback port, served unchanged `/mo-option-chain` and `/mo-option-premium-plane` OpenAPI routes, then stopped |
| HTTP route/DTO/OpenAPI; four Dataset Kernel/Provider/Service/SQLite; all Snapshot Product and Research boundary/runtime tests | Included in full pytest result |
| Frontend `npm install --ignore-scripts` | Passed; lock contents unchanged |
| Frontend `contract:generate` and `contract:check` | Passed; both OpenAPI and generated TypeScript contents unchanged |
| Frontend test, build, lint | Passed: 15 test files / 66 tests; production build completed |
| Authority links and heading anchors | 123 Markdown files, no findings; topology/reachability tests passed |
| Bootstrap syntax | Git Bash `bash -n` and PowerShell parser passed |
| Relocation/reference/diff audit | Every original tracked file accounted for; the baseline included local-state safeguards (removed by final cleanup) and preserved wire text; `git diff --check` passed |

## Baseline limits

Two existing symlink tests remain **skipped**, not passed: CLI Research package discovery and Research output-layout symlink rejection. Windows returned WinError 1314 (no symlink-creation privilege). Ordinary discovery/output and boundary tests passed. Linux/WSL bootstrap execution was not exercised on this Windows host; both scripts passed syntax checks and Windows root install/readiness/launcher steps were exercised. No Linux runtime acceptance is claimed.

The unchanged frontend graph reports one existing npm audit high-severity transitive `source-map-js` finding. Dependency upgrades are outside this migration's explicit version-preservation constraint; no automatic audit fix was applied. Vite reports a large production-chunk warning; pytest reports a third-party Starlette/httpx deprecation warning. Neither warning indicates a namespace/path failure.

## Final cleanup verification and merge assessment

Checks below were executed for this cleanup on Windows with the existing root Poetry environment; no real Source requests or user-cache operations were performed.

| Check | Result |
| --- | --- |
| Root `poetry run pytest -q -rs` | **1417 passed, 2 skipped**, 66.62 seconds; the seven removed cases exclusively tested retired local-state migration behavior |
| `poetry run ruff check .` / `poetry run mypy` | Passed; mypy checked 186 source files |
| Frontend `npm run test -- --run` | 15 test files / **66 tests passed** |
| Frontend `contract:check`, `build`, `lint` | Passed; committed OpenAPI / TypeScript artifacts unchanged |
| CLI doctor, datalake list, research list, Study `--help` | Passed; canonical layout and root environment ready |
| External temporary cwd / installed `python -I` | 20 packages/services import successfully; retired `lab`, `market_snapshot`, `backend_api` namespaces absent; console entry remains `ui_cli.cli:main` |
| Canonical runtime paths with historical state present | Temporary fixtures passed with canonical stores both absent and present: Dataset paths, credential loading, Raw read/write, Observation paths and Research config work independently; old credential is never adopted; historical fixture hashes unchanged |
| Authority navigation / links / anchors | Full topology suite passed; all local links and heading anchors passed across 122 tracked Markdown files, excluding `_temp_docs` |
| Bootstrap syntax | PowerShell parser and Git Bash `bash -n` passed |
| Final reconciliation / diff review | No migration helper/guard references remain; seven module layouts and public contracts retained; no credential or runtime artifact staged; `git diff --check` passed |

The two existing symlink scenarios remain skipped for WinError 1314 and are not counted as passed. Linux/WSL bootstrap execution remains unverified. The existing Starlette/httpx deprecation and Vite chunk-size warnings remain non-blocking; dependencies and locks were not changed.

No blocking regression or authority/implementation gap was found. The branch is ready to merge into local `develop` at `a71b5f9b7316007bf7f45297f4f01ee2e2e8255c`, which is an ancestor and permits a fast-forward merge. This assessment covers the verified Windows scope; a changed target branch still requires normal review/CI. This task commits the cleanup but does not merge, push or deploy it.
