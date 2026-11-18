# ui_web directory ownership

Specializes [module architecture](ARCHITECTURE.md) and preserves [Presentation boundaries](presentation-architecture.md).
This is the canonical directory contract. [Demo authority](demo/ARCHITECTURE.md) owns
current Demo boundaries and navigation. The placement below is implemented.
Current Bundle/page identities and delivery evidence enter the Demo authority,
not a parallel inventory or release verdict here.

## Ownership

```text
ui_web/
  research-map/       Strategy Research Map definition, schema and build-time validation
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

`demo/` is the only formal Demo. DDB-00 retired historical V1 and Public/Private V2 code and data.
Publication follows the root personal-study policy; preserve truthful source disclosure,
disclaimers, credential safety and artifact integrity.

## Data and build boundary

**One Complete Business Result -> One Bundle -> One Hash.** One Manifest indexes the
registered Bundles under [Bundle authority](demo/BUNDLES.md). Multiple HTTP requests may assemble one complete
business Result Bundle; request count does not determine Bundle count. SHA-256 binds exact bytes.
Formal producer contracts continue to own Result meaning and DTOs.

Python generation is an explicit operator action against the local formal HTTP application, using
repository-root Python tooling and normal authentication. It captures official results without
direct service/projection invocation as an alternate generation path. No mock API, finance engine,
second backend or second frontend project is introduced. Any missing formal HTTP capability is a
reported blocker, not permission to expand HTTP semantics in this structural work.

Build Preflight independently checks Manifest/Bundle completeness, identity, envelope,
formal business Result contracts, associations and exact-byte SHA-256. Bundle validators own
packaging/integrity; feature validators own formal Results; Preflight schedules both.
Required failures stop the whole Demo build. Static dependency isolation and deployment
Artifact Verification retain their own responsibilities.
Legacy Publication Rights Gates, Evidence Review and independent review records are not Demo Build
prerequisites. Legacy Envelope validation has been removed.
Build never invokes Python, generates results or contacts an
online business HTTP service. Browsers consume static data and shared Presentation only: no financial
computation, Auth/API requests, polling, preflight or server Run lifecycle. Preserve the admitted
routes and existing local interactions under [workspace authority](workspace.md#static-routing-specialization).
Runtime and result meaning remain with the Demo and business authorities.

## Deployment and lifecycle

Demo build is independent of deployment configuration and credentials. Deployment consumes a verified
artifact and receipt; it does not regenerate data or rebuild scanned bytes. Pages-specific environment
inspection, upload/online verification and release support belong to `deploy/`; workflow definitions
remain under repository `.github/workflows/`. Local Online deployment remains supported independently.

The user selected a hard cutover: remove V1 recovery and do not add previous-generation recovery or
long-term build-history retention. Old ignored build outputs are not current inputs.
This does not authorize deleting formal committed evidence, source, raw/external data, Dataset caches,
credentials or another environment's data. Existing exact-artifact verification, truthful provenance,
distribution bindings and deployment permissions remain required. No production declaration is inferred.

## Maintenance

Directory ownership changes here; current Demo design changes in its specialized authorities.
Runtime capability,
Examples, authenticity and release semantics stay with their narrow existing owners. Move those
authorities and repair inbound/outbound navigation with their implementation, without parallel owners.
Only one formal Demo generation is retained. Superseded Demo documents retire after extracting
valid Authority; Git History preserves their original conclusions. No demo/history tree is planned.
Independent business results, research evidence and data are preserved. DDB-00 retires all legacy runtime entries.

## Build outputs

Online uses `.build/online`; independent static suites use `.build/tests/<suite>`.
Demo output belongs under `.build/demo`. Old ignored outputs are not build inputs.
Historical cleanup observations remain in Git history and are not a current publication verdict.
