# DataLake Source Experiments authority

This document uniquely owns experimental Source isolation, permissions and formal admission. It inherits [DataLake architecture](ARCHITECTURE.md) and the [repository topology](../ARCHITECTURE.md#naming-and-transition-authority). It does not change V1 Kernel, Provider, Dataset, Persistence or public Application contracts.

## Purpose and filesystem ownership

The area is `data_lake/experiments/`, for validating external sources, APIs, fields and acquisition behavior not yet formally integrated. It is isolated from formal runtime wiring; its [entry](experiments/README.md) only provides navigation and isolation guidance.

An Experiment is exploratory integration work, not a formal Dataset, Provider public capability or new Shared Kernel role. Successful acquisition does not establish reusable Source Facts, completeness proof or a stable Public Application Service. Experimental output and credentials obey repository rules excluding runtime artifacts and secrets from Git.

## Isolation and consumer restrictions

- An Experiment does not automatically become a Dataset or acquire Dataset Public Application Service identity. Location under `data_lake` or Python importability does not publish a capability.
- Experiments must not alter Kernel or existing Dataset public contracts, request/result, fact meaning, completeness, failures or storage lifecycle.
- Formal Kernel / Provider / Dataset code and Research, Snapshot, Modeling, HTTP, CLI or other formal consumers must not use Experiments as stable runtime dependencies or necessary service prerequisites. Wrappers, private imports and CLI delegation do not bypass this restriction.
- Experiments do not enter the formal [Dataset catalog](DATASETS.md) or masquerade as supported Dataset service/CLI selections. Existing dependency directions and public boundaries remain intact.
- Do not prebuild an experiment framework, registry, persistence lifecycle, automatic promotion, generic executor or new Source / Dataset abstraction. Concrete experimental code serves only an explicit validation need.

## Admission as formal Source Facts

Reusable formal Source Facts must enter through the existing Dataset authoring path: [module entry](ARCHITECTURE.md) to [Dataset catalog](DATASETS.md) to the owning Dataset authority, under the [Composition contract](COMPOSITION.md), [Domain and completeness invariants](DOMAIN_MODEL.md), [Application and failure contract](APPLICATION.md) and [Source / Repository ports](PORTS.md).

First encode the owning Dataset, fact identity/scope/window/normalization/completeness, Source/Provider responsibilities and public request/result/view in its canonical authority. Bind the existing six roles and any explicitly authorized prerequisites; the owning Dataset remains the sole owner of concrete fact and completeness semantics. Persistence and provider execution follow [Persistence authority](PERSISTENCE.md) and the actual Provider authority as needed. Some successfully fetched rows never replace a completeness or failure contract.

Formal publication requires authority reconciliation, formal implementation and producer/consumer validation before consumers depend on the published public boundary. Moving code, registering a name or running an experiment successfully does not promote it. This contract authorizes no automatic experimental cache migration, API expansion or change to frozen V1 invariants.
