# Approved Workbench Tasks

This catalog navigates user-approved definitions under the [Task contract](../contracts/TASK.md).
It is not a runtime registry, approval service or capability discovery implementation.
Outcomes live exclusively in Runs, never in these definitions.

| Task | Version | Authority | Task-local implementation |
| --- | --- | --- | --- |
| `historical_return_observation` | `1` | [Task entry](historical_return_observation/ARCHITECTURE.md) | G1 Backend Ready; G3 Capability Discovery; G4 Workflow Planning and Persistence; G5 Authorized Execution |

Task-local implementation is not proof of current backend compatibility. V1's anonymous
G1/G3 path is blocked by repository HTTP authentication; read the
[Task compatibility entry](historical_return_observation/ARCHITECTURE.md#current-operational-compatibility)
before attempting a new Run. Existing Runs and historical results remain valid evidence.
