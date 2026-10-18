# Repository Naming Implementation Handoff

This is an engineering handoff and drift register, not a business authority. Canonical identities, namespaces, runtime and dependency direction belong to [repository architecture](ARCHITECTURE.md#naming-and-transition-authority); module contracts remain reachable through current navigation. The reference baseline is `develop` commit `f2f66644e9ef04d7e9b83e2a177b5f718badc462`.

## Current drift

This Goal encodes decisions and reconciles authority only. Directories, installed imports, source, tests, runtime configuration and operational paths still use the current layout. Old labels in existing authority identify the same owners, not a competing target architecture. Target imports are not yet promised to run; no compatibility shim is introduced here.

All seven top-level directory moves and three Python namespace changes remain pending. Existing `data_lake`, `market_research` and reserved `market_modeling` namespaces stay unchanged. Modeling has no independent authority: move only existing content, without creating a framework, empty package or internal design. Target `data_lake/experiments/` is not materialized; [Experiments authority](data-lake/EXPERIMENTS.md) owns isolation and formal admission. DataLake V1 business architecture remains frozen; its prior business-conformance conclusion does not claim this naming migration is implemented.

## Implementation Goal scope

| Engineering scope | Responsibility |
| --- | --- |
| Module filesystem | Apply the repository's seven directory mappings. Preserve internal module / Provider / Dataset / Product / feature co-location of authority, implementation and tests. Move only existing Modeling content. |
| Python namespaces and consumers | Migrate `market_snapshot` to `data_snapshot`, `lab` to `ui_cli`, `backend_api` to `ui_http`, including production, consumers, scripts, tests, dynamic import/module execution strings and first-party tooling. Preserve Product/Dataset identity and service/request/result/failure semantics; do not redesign facades. |
| Root Python tooling | Align package registration, source roots, pytest/Ruff/mypy paths and script entry. Keep distribution `hg-market-state-lab`; switch the entry to `ui_cli.cli:main` while retaining executable `lab`. Use root Poetry only. Update lock metadata only if tooling requires it; do not upgrade dependencies as part of naming. |
| Launchers and local environment | Align CLI path resolution, doctor expectations, HTTP launcher, Research discovery/runners, frontend cwd, bootstrap, Codex environment, CI if present, ignore rules and `.worktreeinclude`. Audit `.env` fallback, Dataset caches, Snapshot Raw/output and relative/absolute paths. Explicitly arrange preservation/switching of untracked local data and credentials, without committing secrets or silently deleting/rebuilding caches. Existing DataLake Persistence compatibility/rebuild rules remain authoritative; a path move is not a schema migration. |
| HTTP and frontend tooling | Align npm scripts, backend paths/imports for OpenAPI generation/check, Vite and related tooling. Preserve endpoints, DTOs, OpenAPI wire semantics, proxy behavior and frontend interaction/display. Update generated artifacts only when the existing feedback loop requires it. |
| Experiments isolation | Establish the target isolated area without a framework, registry or lifecycle. Keep formal runtime free of experimental dependencies. Formal Source Facts still require existing Dataset authoring and completeness contracts. |
| Authority and verification paths | After physical migration, consistently switch root/local navigation, AGENTS, catalogs, specialized filesystem/namespace references, README/DEVELOPMENT/usage examples and topology/colocation checks to real target paths. Clear obsolete transition notes and update drift. Do not mechanically rename Product/Dataset IDs or wire fields. |

This scope excludes business model redesign, Source replacement, calculation/failure changes, Research visualization relocation and Modeling internals. Any newly discovered semantic gap returns to its narrow canonical owner before implementation; string replacement cannot decide business semantics.

## Validation and delivery responsibilities

Use the root environment and each migrated local AGENTS policy. Paths linked here describe current owners; mechanically translate verification paths after moving directories.

- **Repository/runtime owner:** run root `poetry install`, verify installed imports including an isolated interpreter from a temporary cwd, console installation, root `poetry run pytest`, and affected Python Ruff/mypy scopes. Verify distribution identity, unique root environment and all registered source roots. Pytest pythonpath alone cannot prove installation. Check Windows native and Linux bootstrap/launcher resolution; report any platform that could not be exercised.
- **DataLake owner:** follow [local verification](data-lake/AGENTS.md) for Kernel, Provider, four Datasets, public imports, CLI consumers and architecture boundaries. Preserve V1 completeness, per-unit atomic commits, read-only behavior, failure taxonomy and rebuild-only compatibility. Use fake Sources and temporary SQLite, not real caches; renaming does not require new live-Source acceptance.
- **Snapshot/Research owners:** follow [Snapshot rules](market-snapshot/AGENTS.md) and [Research rules](market-research/AGENTS.md) for public services, upstream imports, authority topology/colocation, Study discovery/forwarding and dependency direction. Preserve shared Snapshot capabilities, Raw ownership and Research DataLake-first/no-fallback contracts.
- **CLI owner:** run the migrated `lab/tests` scope and check `lab --help`, hierarchy, arguments, doctor, serve, research and datalake delegation/exit codes. Executable identity remains unchanged. Readiness checks need no live Source calls or running services.
- **HTTP/Web owners:** follow [HTTP rules](backend-api/AGENTS.md) and [Web rules](web-ui/AGENTS.md): backend pytest/Ruff/mypy; frontend `contract:check`, test, build and lint. Confirm unchanged endpoint/DTO/OpenAPI, interaction and presentation behavior. Verify both producer and consumer for cross-module seams.
- **Authority reconciliation owner:** check affected Markdown relative links and anchors, root reachability, old-identifier scan, architecture tests, `git diff --check` and the complete diff. Distinguish historical/external identities, executable `lab`, distribution name and genuine incomplete migration; never blindly replace every old identifier.

Report actual filesystem/namespace status, local artifact switching arrangements, executed validation and unverified scope. Only after implementation and verification should navigation uniformly use target paths. Completion of this authority Goal permits starting migration; it does not claim migrated runtime readiness.
