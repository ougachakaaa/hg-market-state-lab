# Research public upstream authority

This contract owns source selection, public consumption permission, input completeness,
provenance and upstream failure handling. It inherits [module boundaries](ARCHITECTURE.md).
DataLake operations remain owned by [APPLICATION.md](../data_lake/APPLICATION.md);
Dataset contracts are reached through the [DataLake catalog](../data_lake/DATASETS.md).
Snapshot public Products are reached through its [catalog](../data_snapshot/CAPABILITIES.md).

## Design-time source selection

```text
Required fact slice
    → inspect published DataLake Dataset public contracts FIRST
        → semantically sufficient: bind exact Dataset public service
        → insufficient: record reason, inspect Snapshot public Products
            → suitable: bind exact Product public application contract
            → unavailable: declare Upstream Capability Gap
```

DataLake-first is a design-time capability decision, never runtime fallback. Sufficiency
requires legally published facts, scope/window/population and verifiable completeness,
without substantially reimplementing canonical Snapshot Product preparation. Convenient
Snapshot APIs or similarly named fields do not justify bypassing sufficient DataLake
capabilities. Missing caches, runtime unavailability and execution failures do not mean
semantic insufficiency. [DataLake Experiments](../data_lake/EXPERIMENTS.md) are not formal
public capabilities and cannot satisfy a capability gap.

Each concrete case must record required facts, reviewed public capabilities, the exact
selected request/result/failure boundary and any DataLake insufficiency reason before
choosing Snapshot. A missing reusable fact/public completeness capability is a DataLake
owner gap; a missing canonical prepared Product is a Snapshot owner gap. Record the
missing capability, reviewed contracts, owner and effect on readiness. Do not implement
around the gap using private access or extend upstream behavior implicitly.

## Public access and functional permissions

Only Input Preparation acquires upstream market facts. It may call one or more explicitly
selected Dataset public Application Services or Snapshot public Product boundaries.
Observation Construction consumes prepared facts; analysis and reports cannot secretly
acquire them, including via helpers that hide upstream I/O. These are responsibilities,
not a mandatory adapter hierarchy or generic gateway.

Research never directly accesses external market-data providers (including Tushare),
provider SDKs/clients/HTTP endpoints, tokens or credentials. It never imports upstream
Source adapters, Repository objects, private Preparation, Capture or Raw infrastructure,
reads upstream SQLite tables/private storage, or uses CLI/serialized JSON round-trips as
a Python data interface. Shared dependencies and a shared environment grant no additional
permission. Upstream owners retain acquisition infrastructure, credentials, cache lifecycle,
coverage calculation and canonical deterministic Product preparation.

## Completeness and explicit failure

Input Preparation follows each selected public contract and uses the minimum legal
invocation sequence, not a universal coverage → ensure → export workflow. For DataLake,
the final public export supplies its own coverage proof and payload. Validate identity,
schema/view, scope/window, coverage and required records together; do not combine proof
from one operation with rows from another. If ensure is required, inspect its outcome
and export the same semantic request; ensure success alone is not input proof.

Required incomplete inputs, failed units, prerequisite/integrity/operation failures and
invalid public results fail explicitly. Do not analyze partial data, silently drop required
records, impute facts, reinterpret missing/null as zero or claim absence from an empty
incomplete payload. Only a complete valid result can prove absence; the concrete case
must decide whether that absence or a legitimate null is admissible. Each required
dependency must meet its own contract; separate calls do not imply a common snapshot
or provider-current freshness.

Failure of a selected DataLake capability does not authorize Snapshot substitution;
Snapshot failure does not authorize reconstruction from DataLake. Missing credentials,
timeouts, empty/null values or cache state cannot switch sources, fill holes from another
source or silently change evaluation dates. Any admissible population/date resolution
must be explicit case semantics, never an infrastructure fallback. Source selection may
change only through an explicit methodological/authority decision, with resulting inputs
and execution context recorded.

## Provenance and reproducibility

One semantic fact has one declared canonical upstream owner. Multiple required upstreams
are legal only with explicit fact ownership and completeness for each; no implicit merging,
overrides, freshness guarantees or source-conflict resolution is granted.

ResearchRun records actual semantic requests and public input references: Dataset identity,
public view/schema, scope/window and coverage context, or Snapshot Product identity,
query/result contract and version where published. ObservationSet carries source and
derivation references; results link observations, methods and run context. Exact reproducibility
requirements and sufficient input retention/reference strategy must be decided by the
concrete case; a mutable upstream cache or a window alone is not proof of identical inputs.
No new universal provenance envelope or persistence lifecycle is imposed.

Publicly exposed upstream provenance may be inherited under its contract. Research does
not obtain credentials, provider transport responses, internal paths or Repository objects
to manufacture provenance. No provider wrapper, fallback engine, generic data-source
registry or upstream facade is introduced by this authority.
