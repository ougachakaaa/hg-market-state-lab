# Workbench authority

Workbench is a repository-root, agent-facing operational contract and shared
execution-evidence storage facility. It is outside Market State Lab's business and
interaction module taxonomy: not a frontend, backend, business module or Agent Runtime.
The [repository architecture](../ARCHITECTURE.md) owns runtime and module boundaries.

Workbench owns Task design/approval conventions, shared Task / Run / Gate contracts,
agent execution boundaries, shared Run storage conventions and generic evidence
recording/retrieval. Tasks own operational goals, permitted capabilities and their
own Gates; Runs own concrete execution evidence. Workbench grants no additional
cross-module import or execution permission. Business semantics remain with their owners.

| Concern | Canonical authority |
| --- | --- |
| User-designed, approved and versioned operation definition | [Task contract](contracts/TASK.md) |
| One execution of an exact Task version | [Run contract](contracts/RUN.md) |
| Task-owned check definition and Run-owned outcome | [Gate contract](contracts/GATE.md) |
| File format, publication, integrity and recorder operations | [Storage contract](contracts/STORAGE.md) |

Stable entry is [AGENTS.md](AGENTS.md); practical instructions are in [README.md](README.md).
`run_store.py` is an independently usable standard-library script in the existing
root runtime, not an installed Python package or official `lab` command.

No universal Gate count or ordering exists. Approved Tasks enter through the narrow
[Task catalog](tasks/README.md); their Gates have no global authority here.
The first Task implements its own backend-readiness and read-only capability-discovery
checks and Task-specific validation/persistence of Agent-authored workflows through
pure public Python Research Preview. Authentication, Research execution, visualization,
scheduling and agent orchestration are not implemented by Workbench. Discovery consumes
published HTTP responses; Workbench owns no capability registry or business validation.
