# Demo authority

Specializes [module authority](../ARCHITECTURE.md) and [directory ownership](../STRUCTURE.md).
This is the canonical Demo entry. DDB-01 encodes the design. Collector, Bundle admission,
the new runtime and publication remain unimplemented pending DDB-02 through DDB-05.

## Purpose and ownership

The single Demo presents complete formal business results through shared React Presentation
in an anonymous, read-only static application. Python business modules own all financial
computation, market processing, statistics, research and backtesting. FastAPI is the sole
business-result acquisition boundary for Demo generation (SD-01).

Online calls formal HTTP at runtime. Demo generation explicitly calls formal HTTP locally,
commits captured results, and builds static assets. Both consume the same business contracts
and feature Presentation. Online has no dependency on Demo data or tooling (SD-02).

Demo owns packaging, static composition, admission and build orchestration. Feature owners
retain their generated contracts, pure result validators, presentation state and components.
HTTP owns transport and authentication. Business modules retain result semantics.

## Stable invariants

- Bundles contain a Demo envelope and complete formal business results. Run responses may
  supply their immutable request and complete result without the outer Run lifecycle.
  Multiple formal DTOs may form a static assembly (SD-03).
- One active dataset has one Manifest and one JSON per registered Bundle, independently
  hashed and Git-tracked. Git history retains previous deliveries (SD-04).
- Local generation is an explicit developer action using repository-root Python tooling,
  existing HTTP authentication and formal requests. Single-Bundle and full generation
  preserve valid data on acquisition failure (SD-05).
- Build independently validates completeness, identity, envelope, formal result contracts,
  associations and file SHA-256 before producing the Demo artifact (SD-06).
- Local and CI build share one offline entry and admission standard. Build consumes tracked
  data and outputs ignored `ui_web/.build/demo/` (SD-07).
- Release follows local HTTP generation, validation, local build, static preview, Git commit,
  independent Actions build and verified Pages artifact deployment. UI-only work can reuse
  valid committed Bundles (SD-08).
- Direct cutover maintains one current contract and dataset. DDB-00 retired Synthetic V1 and
  Public/Private V2. Future contract changes update the current delivery directly (SD-09).

The browser loads static resources and runs local presentation interactions. Business HTTP,
Auth, backend preflight, polling and server Run lifecycle belong to generation/Online.
Build Preflight is an offline admission step in the build process.

## Navigation

- [Bundle contract](BUNDLES.md) owns identities, Registry, Presets, Manifest and exact bytes.
- [Build authority](build/ARCHITECTURE.md) owns collection, transactions and build admission.
- [HTTP feasibility](build/HTTP_FEASIBILITY.md) records DDB-01 source evidence and limitations.
- [Implementation handoff](build/HANDOFF.md) defines DDB-02 through DDB-05 boundaries.

Public distribution continues to require truthful source descriptions, authorization and
artifact integrity under existing repository policies. HTTP success and a matching hash
alone do not establish permission to distribute market data.
