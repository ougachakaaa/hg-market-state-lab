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
boundaries. WB-04 implements the narrow [G4 workflow contract](WORKFLOW_PLANNING.md)
under [its request](PLANNING_REQUEST.md), with [separate acceptance](PLANNING_ACCEPTANCE.md).
The exact Task v1 snapshot remains unchanged. Pending execution authorization is an
explicit planning disposition; see that contract's reconciliation. WB-05 implements
[G5 authorized execution and delivery](AUTHORIZED_EXECUTION.md) under
[its request](EXECUTION_REQUEST.md), with [separate acceptance](EXECUTION_ACCEPTANCE.md).
Live execution still requires approval of the exact frozen artifact and side effects.
WB-06 records [natural-language E2E acceptance](wb06/ACCEPTANCE.md), its
[human research report](wb06/REPORT.md), [live readiness](wb06/LIVE_READINESS.md)
and [problem log](wb06/problems.json). Deterministic acceptance and full-history live
acceptance have separate conclusions; these records grant no execution permission.
WB-07's [procedure](wb07/SCENARIO.md), [current acceptance](wb07/ACCEPTANCE.md)
and [problems](wb07/PROBLEMS.md) track the separately commissioned real-market matrix
and persistent cold/warm cache acceptance. Each live G5 needs exact user authorization.

Business meaning remains with the [Research publication](../../../market_research/descriptive/RESEARCH_CAPABILITY.md),
[trailing-return case](../../../market_research/descriptive/cases/trailing_return/ARCHITECTURE.md)
and [Batch contract](../../../market_research/descriptive/BATCH_EXECUTION.md).
The [Research HTTP contract](../../../ui_http/products/research/http-contract.md)
owns paths, operationIds and transport limits; Task G1 consumes that contract.

Only the published descriptive index case is admitted. Long historical questions
remain expressible without implying live readiness or HTTP executability. Neither
Workbench nor this Task owns financial formulas, numerical methods, provider selection,
missing-data policy, acquisition, cache repair or service lifecycle.
