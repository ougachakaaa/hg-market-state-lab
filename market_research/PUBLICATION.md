# Published Research Result authority

## Storage transition status

[Publication storage](PUBLICATION_STORAGE.md#portable-sqlite-target) owns the approved
SQLite replacement. The current POSIX file store remains active until storage WP4/WP5.
The development-time breaking cutover abandons old data without migration, dual reads or
compatibility; it preserves all publication business operations, immutable snapshots,
integrity and association checks, HTTP interfaces and Research Explorer.

This contract specializes [Research architecture](ARCHITECTURE.md) and owns the
publication lifecycle, semantic identity, provenance, integrity and read boundary.
The concrete V1 publication implementation and storage contract is
[Publication storage](PUBLICATION_STORAGE.md); no HTTP endpoint is implied.
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
The store is Research-owned, separate from Workbench RunStore; canonical JSON payload
encoding is independent of its physical storage backend;
publication must be atomically visible as a complete snapshot, refuse overwrite and verify
integrity on read. Storage paths, exact serialization, digest algorithm, API signatures and
failure types are specified by the lower-level implementation contract;
those choices preserve these invariants and the public Layer contract.

## Granular reader and Analysis identity

Research exposes these independent logical read capabilities; names do not prescribe
Python signatures or HTTP routes:

```text
list_publications()
get_publication_manifest(publication_id)
get_analysis(publication_id, analysis_id)
```

A complete validated snapshot may also be retrieved by exact identity. The Manifest is a
navigation summary of publication identity, scope and status, Job summaries with Analysis
references, available ChartView references, and source/provenance summary. It must not
require returning every Observation, StatisticalResult or Layer payload. The reader must
also support materializing an available ChartView independently, without returning all
other analyses or Layers in the publication. A read of one Analysis returns its detailed
payload independently of unrelated payloads.

Each published Analysis has a publication-scoped, unique and stable `analysis_id`, and
explicitly records its original full structural Job identity, exact AnalysisRequest
`request_id` and spec, and source evidence reference. These associations are preserved on
every read. Repeated `request_id` values on different Jobs are distinct Analyses; neither
request ID alone nor array position identifies an Analysis. If multiple source executions
contain the same Job and request, their respective source identities remain explicit and
distinct Analyses cannot collide. Publication owns this address, not the ResearchPlan,
JobResult, BatchResult, Statistics result or Workbench Run identity. Its generation algorithm
is a WP2 storage decision. Different publication IDs do not share an identity namespace.

Manifest references and detailed results resolve only within the specified immutable
publication. The reader validates publication and Analysis identity, exact original
request/spec, Job and evidence association, status and integrity before returning success;
failed, skipped or not-attempted analyses cannot be presented as successful results.
Each read returns validated stored content or an explicit missing, unsupported-version,
corrupt or unavailable failure. A missing Analysis is distinct from a recorded failed or
not-attempted Analysis. No reference grants arbitrary filesystem access, resolves against
another publication, or authorizes access to internal producer storage.

Granular verification must bind the retrieved payload and its references to the same
immutable publication and its validated Manifest, and verify the relevant stored integrity
evidence without requiring transfer of unrelated payloads. It must not silently accept
missing or inconsistent evidence, repair or recompute data. Reads never execute Research,
acquire DataLake facts or invoke Statistics. Query filtering, ordering, pagination, transport
mappings, reference encoding and retention/access to source evidence require explicit
lower-level contracts; no defaults are inferred here.

## IntervalCount projection

The producer-aware adapter may project a successful
[IntervalCountResult](../market_statistics/INTERVAL_COUNT.md#result-and-accounting) to a
categorical BarLayer under the [Visualization contract](../ui_web/VISUALIZATION.md).
The published Analysis retains the complete original StatisticalResult, exact edges, ordered
bin boundaries and inclusion flags, bin counts and frequencies, underflow and overflow
counts and frequencies, `sample_count`, original result association and source evidence.
These facts are not replaced by chart labels or reconstructed from bar data.

One category corresponds to each bin, plus explicit underflow and overflow categories,
in their original statistical order: underflow, bins in edge order, overflow. Include both
outside categories even when their value is zero. Labels must uniquely and unambiguously
identify the exact boundaries and inclusion rules, including the outside inequalities;
display formatting must not round distinct boundaries into an ambiguous label or change
their meaning. The original exact boundaries remain independently accessible with the
Analysis. A projection selects either the published counts or the published frequencies
unchanged, with an explicit y unit. Separate projections must each refer to the same
original published Analysis/result and identify which measure they display. The frontend
may select between such projections without recalculating statistics, changing the
full-sample denominator, or treating missing results as zero.

For example, irregular edges `[0, 1, 3]` yield ordered labels such as `< 0`, `[0, 1)`,
`[1, 3]`, `> 3`, with their actual returned values, including both outside categories.
Equal-width categorical bars express these categories; they do not imply numeric-width
geometry or a density histogram. Statistics remains the sole owner of partition and
frequency semantics; no new numerical method is defined here.

## Stored references and render-ready Views

Publication may store Layer data and View definitions separately and expose publication-
scoped `LayerDataRef` and `ChartViewRef` as opaque references. They are Research-owned
references, not Visualization Layer types, HTTP identities or filesystem paths. Each must
resolve only to the intended immutable publication and its declared object; reject missing,
cross-publication, mismatched or corrupt references explicitly. The Manifest's available
ChartView references must identify the relevant published Analysis associations.

The producer-aware Publication Reader or an explicitly authorized producer-aware delivery
projection resolves the selected View and only its required Layer references, validates
the referenced content and associations, and materializes a complete inline-data ChartView
that conforms to the single [Visualization contract](../ui_web/VISUALIZATION.md). Any
failed resolution or validation fails the View read; do not omit or substitute Layers.
The renderer receives that complete View and never reads Publication references or locations.
This boundary does not grant Visualization knowledge of Research or storage and does not
establish a second Python, HTTP, TypeScript or Plotly Layer schema.

## Consumers and readiness

`ui_http` may use only the Research public reader and project its semantics through its own
read-only HTTP contract; it does not access Research storage directly. Research Explorer
consumes the published HTTP/OpenAPI contract; browsing never causes execution, acquisition or
recomputation. The producer-aware adapter belongs to Research publication, never Statistics
or Visualization. A Workbench Task may separately request publication only with the appropriate
approved operational authority; Workbench evidence is not publication storage.

Concrete V1 JSON, source eligibility, identity, integrity and reader semantics are specified
in [Publication storage](PUBLICATION_STORAGE.md). The implemented read-only delivery is
defined by the [HTTP publication contract](../ui_http/products/research_publication/http-contract.md);
Research Explorer consumes its generated contract. This publication boundary does not change
current execution behavior.

The independent [Futures Basis case](descriptive/cases/futures_basis/ARCHITECTURE.md)
is not admitted to Publication V1 or its current HTTP transport. Its planned
[offline report](descriptive/cases/futures_basis/DELIVERY.md) supplies separate
case evidence and generic Views to ui_web rendering; it is not a
PublishedResearchResult and does not weaken publication admission or integrity.
Future publication/HTTP integration requires explicit versioned extensions.
