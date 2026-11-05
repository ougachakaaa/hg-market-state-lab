# Task contract

A Task is a user-designed, explicitly approved, versioned definition of one type of
operation. It owns goal/scope, required user inputs, allowed project capabilities
and boundaries, Gate definitions and dependencies, AI workflow planning constraints,
expected outputs and acceptance criteria. It must respect repository/module authority.

Agents may propose designs; explicit user approval is required to promote them to
Task authority. Changes require a new version and approval. Runs never update their
parent definition. There is no Task registry, approval service or executable Task
engine in the current implementation; approval evidence is supplied by the caller and
remains subject to human/agent verification, not certified by storage.

The recorder accepts a complete JSON snapshot with these required fields:

| Field | Contract |
| --- | --- |
| `task_id`, `version` | Nonempty strings; exact version identity, no `latest` resolution |
| `approval` | Object: `kind` = `user_approved` or `synthetic`; nonempty `reference` locating approval evidence or identifying a test-only fixture |
| `goal`, `scope` | Nonempty strings |
| `required_inputs`, `allowed_capabilities`, `planning_constraints`, `expected_outputs`, `acceptance_criteria` | Arrays of nonempty descriptive strings; empty arrays explicitly mean none |
| `gates` | Array of definitions: unique nonempty `gate_id`, nonempty `criteria`, `depends_on` array of Gate IDs in this Task |

Gate array order and dependencies belong to this Task, never Workbench. Dependencies
must exist, be unique and form an acyclic graph; execution order/criteria enforcement
remain the executor's responsibility. An empty Gate array is permitted. Additional
JSON fields are preserved verbatim as part of the snapshot, not interpreted as new
storage permissions. JSON values must be finite and use string object keys.

`synthetic` is exclusively a test/demo definition, never approved business authority.
The recorder rejects neither future business vocabulary nor invents any. It records
the exact supplied snapshot and a deterministic SHA-256 digest; the snapshot itself
is sufficient, so no mutable external Task reference is relied on for replay.
