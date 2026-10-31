# Published Research Result authority

This contract specializes [Research architecture](ARCHITECTURE.md) and owns the
publication lifecycle, semantic identity, provenance, integrity and read boundary.
It is prospective authority; no publication runtime or HTTP endpoint is implied.
Execution and result association remain under [Descriptive execution](descriptive/EXECUTION.md)
and [association](descriptive/RESULT_ASSOCIATION.md). The domain-neutral Layer contract
is owned by [Visualization](../ui_web/VISUALIZATION.md).

## Identity and scope

A PublishedResearchResult is a validated, immutable, reproducible, queryable Research
output, explicitly published from retained, completed research evidence. It is distinct
from a BatchResult, Workbench Run, raw Observation and StatisticalResult. Research owns
its identity and versioned publication schema; an identifier names one immutable published
snapshot, never a mutable latest alias or an execution ID. Publishing changed content
requires a new identity; collision with different content is a failure, never overwrite.
A publication may refer to multiple source executions only when their scope and associations
are explicitly represented and validated. Publication is not a generic computation cache,
Study, ResearchRun, RunStore record or replacement for original evidence.

Each snapshot must retain, in a versioned structure:

- its unique identity, schema version and publication creation context;
- the exact declared research scope: case/definition and version, subjects, parameters,
  horizons and units, window and inclusion/calendar semantics, and requested analyses;
- actual published results with exact request/spec association, job identities and outcome
  status, coverage, exclusions, limitations and units needed to interpret them;
- source references sufficient to locate and verify original evidence, including source
  identity and integrity digest, plus definitions, input/fact provenance, derivations,
  method/version and execution context needed to reproduce or audit the result;
- explicit visualization projections, each with a stable association to its source result,
  valid versioned Layer data, and enough mapping context to interpret coordinates.

Source references and integrity checks do not guarantee external evidence remains available;
missing or unverifiable required evidence prevents publication. Preserve failure, skipped
and incomplete outcomes honestly; do not label partial results complete or fabricate absent
values. A publication may represent partial research only when its scope, statuses, missing
results and limitations explicitly disclose that fact. Statistical values and calculations
remain exclusively owned by Statistics; Research owns scope, empirical meaning, association,
coverage and interpretation. Upstream producers remain authoritative for their own facts.

## Separate publish and read operations

Execution produces its existing in-memory result and never implicitly publishes. A separate,
explicit publication operation receives retained evidence and its references, verifies
scope, result linkage, provenance and integrity, creates producer-owned projections and
validates every Layer before making the whole immutable snapshot visible. It fails explicitly
on malformed, inconsistent, missing or unverifiable input and never repairs or recomputes it.
Publication has no authority to execute Research, acquire DataLake facts or invoke Statistics.
The initial intended store is JSON-based and Research-owned, separate from Workbench RunStore;
publication must be atomically visible as a complete snapshot, refuse overwrite and verify
integrity on read. Storage paths, exact serialization, digest algorithm, API signatures and
failure types must be specified in a lower-level implementation contract before WP2 coding;
those choices must preserve these invariants and the public Layer contract.

Research exposes a public read-only boundary to enumerate available publication identities
and retrieve one complete snapshot by exact identity. Reads return validated stored content or
an explicit missing, unsupported-version, corrupt or unavailable failure; they never execute,
acquire, recompute, mutate or silently repair. Query filtering, ordering, pagination and
transport mappings require explicit contract decisions before exposure; no defaults are
inferred here. References are not permission to read internal producer storage. Retention
and access to source evidence must be stated for each published source.

## Consumers and readiness

`ui_http` may use only the Research public reader and project its semantics through its own
read-only HTTP contract; it does not access Research storage directly. Research Explorer
consumes the published HTTP/OpenAPI contract; browsing never causes execution, acquisition or
recomputation. The producer-aware adapter belongs to Research publication, never Statistics
or Visualization. A Workbench Task may separately request publication only with the appropriate
approved operational authority; Workbench evidence is not publication storage.

WP2 must specify concrete JSON schema, reference resolution/retention, digest and atomic
storage semantics, source eligibility, identity generation and exact public API/failures
before implementation. WP3 must define HTTP routes, DTO projection and status mappings,
then WP4 must generate consumer artifacts. These details are not established by WP0, and
this prospective boundary does not change current execution behavior.
