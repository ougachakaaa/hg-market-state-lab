# Workbench agent entry

Inherit [repository policy](../AGENTS.md). Read [identity and ownership](ARCHITECTURE.md)
first, then only the relevant contract: [Task](contracts/TASK.md),
[Run](contracts/RUN.md), [Gate](contracts/GATE.md), [storage](contracts/STORAGE.md).
[README](README.md) is usage guidance, not semantic authority.

Agents may propose Task designs. Only explicit user approval promotes a proposal
to approved, versioned Task authority. Never infer approval from a successful Run,
an approval field supplied to the recorder, or a synthetic test fixture. A Run
cannot edit its Task. Approved Tasks are discoverable through the
[Task catalog](tasks/README.md); follow the selected Task's authority before execution.
Task approval and historical PASS evidence are not current backend compatibility.
Before attempting a selected Task, read its authority and current operational status;
do not bypass authentication or present fixture evidence as current live integration.

Workbench scripts use the repository-root Python environment. Do not add a package,
environment, server, database, `lab` group, planner or execution engine. Do not import
business modules into the generic recorder. Executing a future Task still requires
reading each capability owner's authority and local policy.

For changes, encode semantics in the narrowest contract before implementation.
From repository root run:

```text
poetry run pytest workbench/tests
poetry run ruff check workbench
poetry run mypy workbench/run_store.py
poetry run python workbench/tests/acceptance_example.py
```

Tests use temporary storage; the acceptance example writes only synthetic evidence
under ignored `workbench/.runs/`. Review the complete diff and reconcile root
navigation, contracts, script behavior and acceptance evidence. Do not modify market
runtime data to validate this facility.
