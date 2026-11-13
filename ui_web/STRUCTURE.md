# ui_web directory ownership

Specializes [module architecture](ARCHITECTURE.md) and preserves [Presentation boundaries](presentation-architecture.md).
This is the canonical directory contract approved in structural WP0. It describes the target;
the [migration audit](STRUCTURAL_MIGRATION.md) records current paths, dependencies and cutover gates.
WP0 changes documents only. Existing commands and paths remain operational until their assigned WP.

## Ownership

```text
ui_web/
  src/                Online Web and shared Presentation, including formal offline reader
  demo/
    runtime/          one anonymous read-only composition and static loading
    bundles/          one manifest and independently hashed Result bundles
    build/            explicit generation, offline validation and Vite build tooling
  tests/              specialized harnesses, browser suites, fixtures and auxiliary configs
  scripts/            general development and generated-contract tooling
  deploy/             local deployment and GitHub Pages support
  .build/             all generated builds, build caches and acceptance outputs; Git ignored
  node_modules/       npm dependencies at ui_web root
  package.json
  package-lock.json
```

One npm project and dependency graph remain. Root Online entry/configuration and package tooling
may remain at module root. Specialized test configs belong to `tests/config/`; Demo configuration
belongs to `demo/build/`. Co-located feature unit tests and feature Authority remain with their
owner; `tests/` is not a demand to move every unit test. Shared feature validators, pure projections,
local presentation state and charts remain in `src/`, never copied into Demo. Demo consumes feature
public Presentation entries; Online must not depend on Demo or test harnesses.

`demo/` is the only formal Demo. Historical V1, Private V2 and separate Public/Private runtimes
are migration inputs, not enduring products. Private admission restrictions are preserved when
retiring their implementation; restricted material does not become a public Bundle by moving it.

## Data and build boundary

**One Result → One Bundle → One Hash.** A single Manifest indexes all formal Demo Bundles.
Each Bundle contains one complete formal Result plus its required identity/provenance association;
it does not create another business DTO. SHA-256 binds exact Bundle file bytes. Manifest metadata
associates route selections, result identities, hashes and existing review bindings. Multiple HTTP
results needed by Explorer/catalog are separate bundles referenced by the same Manifest; navigation
descriptions do not require invented financial Results. Formal producer contracts still own results.

Python generation is an explicit operator action against the local formal HTTP application, using
repository-root Python tooling and normal authentication. It captures official results without
direct service/projection invocation as an alternate generation path. No mock API, finance engine,
second backend or second frontend project is introduced. Any missing formal HTTP capability is a
reported blocker, not permission to expand HTTP semantics in this structural work.

Vite verifies hashes, completeness, formal result compatibility and required review associations
before consuming existing Bundles. Build never invokes Python, generates results or contacts an
online business HTTP service. Browsers consume static data and shared Presentation only: no financial
computation, Auth/API requests, polling, preflight or server Run lifecycle. Preserve all seven formal
routes and existing local interactions. Runtime, Example meaning and distribution decision remain
owned by the existing [Demo Runtime](src/demo/ARCHITECTURE.md), [Examples](src/demo/EXAMPLES.md) and
[Authenticity](src/demo/AUTHENTICITY.md) contracts pending their explicitly staged reconciliation.

## Deployment and lifecycle

Demo build is independent of deployment configuration and credentials. Deployment consumes a verified
artifact and receipt; it does not regenerate data or rebuild scanned bytes. Pages-specific environment
inspection, upload/online verification and release support belong to `deploy/`; workflow definitions
remain under repository `.github/workflows/`. Local Online deployment remains supported independently.

The user selected a hard cutover: remove V1 recovery and do not add previous-generation recovery or
long-term build-history retention. Clean identifiable historical build outputs at WP4, not WP0.
This does not authorize deleting formal committed evidence, source, raw/external data, Dataset caches,
credentials or another environment's data. Existing exact-artifact verification, truthful provenance,
distribution bindings and deployment permissions remain required. No production declaration is inferred.

## Maintenance

Directory ownership changes here; migration state and gates change in the audit. Runtime capability,
Examples, authenticity and release semantics stay with their narrow existing owners. Move those
authorities and repair inbound/outbound navigation with their implementation, without parallel owners.
Historical acceptance retains its original revision, commands and conclusions, with a migration note
where necessary. It is not evidence that the new structure has passed.
