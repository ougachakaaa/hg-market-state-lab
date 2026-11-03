# Approved Workbench Tasks

This catalog navigates user-approved definitions under the [Task contract](../contracts/TASK.md).
It is not a runtime registry, approval service or capability discovery implementation.
Outcomes live exclusively in Runs, never in these definitions.

| Task | Version | Implemented operations | Main inputs | Output types | Entry points |
| --- | --- | --- | --- | --- | --- |
| `historical_return_observation` | `1` | Historical trailing-return distribution observation: G1 backend readiness; G3 capability discovery; G4 workflow planning/persistence; G5 separately authorized execution. G2/G6 deferred. | Backend target/timeout (documented defaults permitted); for research, explicit supported index identities, trading-session horizon(s) H, inclusive date range(s), statistical requests/parameters and failure policy; separate execution authorization. | Readiness/discovery evidence; frozen workflow/preview; research statistics and readable report, with coverage and limitations. | [Authority](historical_return_observation/ARCHITECTURE.md); [usage and runtime entry points](historical_return_observation/README.md) |

The Task entry links its exact definition and approval evidence. Follow its usage
guide for Task-specific execution scripts in the repository-root Python environment.
Synthetic examples and test fixtures are not approved Tasks; historical Runs and
research results are not separate Task definitions.

[RunStore](../contracts/STORAGE.md) preserves original execution evidence. A Task's
results package organizes research findings and references that evidence; it does not
replace the frozen Run artifacts or authorize another execution.
