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

**One Complete Business Result -> One Bundle -> One Hash.** One Manifest indexes all
seven current Examples as seven Bundles. Multiple HTTP requests may assemble one complete
business Result Bundle; request count does not determine Bundle count. SHA-256 binds exact bytes.
Formal producer contracts continue to own Result meaning and DTOs.

Python generation is an explicit operator action against the local formal HTTP application, using
repository-root Python tooling and normal authentication. It captures official results without
direct service/projection invocation as an alternate generation path. No mock API, finance engine,
second backend or second frontend project is introduced. Any missing formal HTTP capability is a
reported blocker, not permission to expand HTTP semantics in this structural work.

Future Bundle admission verifies only the Manifest and Bundle SHA-256. Business DTO/Result
validation, static dependency isolation and deployment Artifact Verification are separate concerns.
Legacy Publication Rights Gates, Evidence Review and independent review records are not Demo Build
prerequisites. This target decision does not change current validation code in WP1A.
Build never invokes Python, generates results or contacts an
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
Only one formal Demo generation is retained. Superseded Demo documents retire after extracting
valid Authority; Git History preserves their original conclusions. No demo/history tree is planned.
Independent business results, research evidence and data are preserved. WP1A retires no runtime or V1 archive.

## WP1A build outputs

Current Online build/preview uses `.build/online/`; Public Demo packaging uses `.build/demo/`
(site, receipt and verification evidence). Temporary V1 uses `.build/tests/v1/`; seven static
suites use `.build/tests/<suite>/`, compatibility probes use unique subdirectories there.
Vite and configurable TypeScript caches use `.build/cache/`. Third-party dependency caches
remain npm-owned. Explicit external delivery roots and OS temporary browser/backend runtime
roots retain their semantics. WP1B owns source/config/test relocation; WP1A moves none of them.

## Reviewed input checkout bytes

Root `.gitattributes` constrains the exact files in `scripts/public_payload_inventory.json`
and Public review evidence: reviewed text uses LF on every platform; binary archives use
`-text`. Keep these rules aligned when admitting a new reviewed input. Runtime verification
continues to hash exact file bytes without normalizing them or rewriting reviewed digests.

## WP1B current test ownership

Specialized configs, static/Visualization harnesses and browser/isolation/fixture/tooling/deploy
tests now occupy `tests/` as defined above. Feature unit tests, setup and Production Presentation
retain their owners. Root Online and transitional V1/private/public engineering entries remain.
Current paths and completion gates belong to the [migration audit](STRUCTURAL_MIGRATION.md);
file-level movement and verification are recorded in [WP1B acceptance](WP1B_ACCEPTANCE.md).
