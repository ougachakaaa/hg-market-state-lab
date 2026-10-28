# Historical Return Observation Task

Task identity: `historical_return_observation`, version `1`, user-approved by the
WB-02 Goal request preserved in [design approval evidence](DESIGN_REQUEST.md).
The request explicitly commissions the approved Task and its six Gates; it authorizes
G1 implementation/acceptance, not live Research or paid-data access. Storage does not
certify that approval. Changes to this definition require a new approved version.

The canonical complete, machine-loadable Task authority is [task.json](task.json),
under the shared [Task](../../contracts/TASK.md), [Run](../../contracts/RUN.md) and
[Gate](../../contracts/GATE.md) contracts. It owns operational scope, inputs, permitted
capabilities, planning constraints, six Gate definitions/dependencies and acceptance.
It contains no execution outcomes. Run creation freezes the entire JSON definition.

Read the [G1 contract](BACKEND_READY.md) for the Task-specific checker, failure map
and evidence procedure. [Usage](README.md) owns commands; [WB-02 acceptance](ACCEPTANCE.md)
owns actual verification. WB-03 adds the narrow [G3 discovery contract](CAPABILITY_DISCOVERY.md)
and [its acceptance](DISCOVERY_ACCEPTANCE.md) for the already approved discovery slice,
preserving the exact version-1 snapshot. These documents neither expand public business
boundaries nor implement G4/G5.

Business meaning remains with the [Research publication](../../../market_research/descriptive/RESEARCH_CAPABILITY.md),
[trailing-return case](../../../market_research/descriptive/cases/trailing_return/ARCHITECTURE.md)
and [Batch contract](../../../market_research/descriptive/BATCH_EXECUTION.md).
The [Research HTTP contract](../../../ui_http/products/research/http-contract.md)
owns paths, operationIds and transport limits; Task G1 consumes that contract.

Only the published descriptive index case is admitted. Long historical questions
remain expressible without implying live readiness or HTTP executability. Neither
Workbench nor this Task owns financial formulas, numerical methods, provider selection,
missing-data policy, acquisition, cache repair or service lifecycle.
