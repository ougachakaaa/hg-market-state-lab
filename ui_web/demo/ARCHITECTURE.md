# Demo authority

Specializes [module authority](../ARCHITECTURE.md) and [directory ownership](../STRUCTURE.md).
This is the canonical Demo entry. DDB-01 encodes the design. DDB-02 supplies the static
Registry, explicit initial Presets and executable offline Bundle admission. DDB-03 supplies
the HTTP Collector and transaction recovery. DDB-04-R1 delivered real captures. DDB-04 implements the sole runtime and offline build.
DDB-06 extends DDB-05 verified artifacts with release requirements and dedicated-branch
publication. Actual releases require their own receipts and online acceptance.

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
- [HTTP catalog](../../ui_http/HTTP_PRODUCTS.md) owns the formal capture operations.
- [Release Runbook](release/RUNBOOK.md) owns publication and recovery.

Publication follows the root personal-study policy. Preserve source disclosure,
disclaimers and safety checks. Release contracts live in
[deployment authority](../deploy/ARCHITECTURE.md).

## DDB-04 runtime

The sole runtime lives in demo/runtime and consumes the validated private snapshot.
Its adapters reuse feature public validators and Presentation. Identity contains Bundle
ID, Preset, contract and actual source description. Ten shared pages use hash routes.
Explorer remains hidden from sidebar navigation.

Build admits all nine Bundles before emitting separate static JS modules. The initial
application contains Shell/navigation and loader references, not all Result payloads or
chart Presentations. Runtime loads only the selected consumer's Presentation, validator
and Bundle. Research Overview consumes Catalog; Data/Backtesting overviews consume no
Result; each business page consumes its own Bundle; Explorer consumes Publications.
Backtesting initially consumes M1, loading Q1 only when selected. Route/component mapping
belongs to runtime composition, not the Bundle Registry or Collector.

Each consumed envelope and formal Result must validate before display. Successful
adaptation and in-flight work are cached within this application instance only; no
browser persistence or online fallback is introduced. Bundle loading and validation
timing is inspectable through local Performance measures: `demo-bundle:<id>:load`
covers the static import and `demo-bundle:<id>:validate` covers envelope validation
and formal adaptation. These diagnostic durations contain no payload data and make
no rendering-time or transfer-compression claim. Resource-loading and invalid-data
failures have distinct safe explanations with explicit retry, never raw diagnostics.
Changing routes/strategy immediately hides the previous result and isolates late
completions. Unavailable resources do not fabricate results or prevent navigation away.
Build still rejects any invalid Bundle globally; deferred runtime validation never
relaxes whole-dataset admission, exact bytes, Manifest identity or release requirements.

Release content requirements enter [Release Requirements](release/ARCHITECTURE.md).

## Calendar Spread L1 integration

[Calendar Spread integration](CALENDAR_SPREAD.md) adds two independent formal HTTP
Result captures and consumes the WP6 public Presentations. The sole active dataset
has nine Bundles; the runtime has ten routes. Capture, identity and offline consumption
requirements remain in that integration contract. No publication is implied or authorized.
