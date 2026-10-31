# Historical Return Observation Task

Task `historical_return_observation` version 1 is defined by the immutable [task.json](task.json); its original approval evidence remains [DESIGN_REQUEST.md](DESIGN_REQUEST.md). Task approval does not authorize live Research. The shared [Task](../../contracts/TASK.md), [Run](../../contracts/RUN.md), [Gate](../../contracts/GATE.md) and [storage](../../contracts/STORAGE.md) contracts apply.

Current Task-specific contracts: [G1 backend readiness](authority/BACKEND_READY.md), [G3 capability discovery](authority/CAPABILITY_DISCOVERY.md), [G4 workflow planning](authority/WORKFLOW_PLANNING.md), [G5 authorized execution](authority/AUTHORIZED_EXECUTION.md), and [research results](authority/RESULTS.md). G2 and G6 remain deferred for version 1 and its frozen Runs. Addressing G6 requires an
explicitly user-approved new Task version or another separately authorized extension under
the shared Task contract; existing snapshots and evidence are never rewritten, and this
authority change itself grants no approval or execution permission. Future publication uses
the [Research boundary](../../../market_research/PUBLICATION.md), not Workbench storage. The [usage guide](README.md) identifies runtime entry points; [results](results/2026_four_index_returns/README.md) are organized research findings, not execution authorization. RunStore owns actual execution history and original evidence.

Research owns the [published capability](../../../market_research/descriptive/RESEARCH_CAPABILITY.md), [trailing return case](../../../market_research/descriptive/cases/trailing_return/ARCHITECTURE.md) and [Batch contract](../../../market_research/descriptive/BATCH_EXECUTION.md); HTTP owns its [transport contract](../../../ui_http/products/research/http-contract.md). Only the published descriptive index case is admitted. This Task owns neither financial formulas, statistics, provider selection, missing-data policy, acquisition, cache repair nor service lifecycle. Long historical questions do not imply live readiness.
