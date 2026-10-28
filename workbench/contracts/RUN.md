# Run contract

A Run is one concrete execution of a specific Task version. It owns its generated
identity, original user request, exact Task snapshot, resolved execution inputs,
caller-supplied AI workflow when applicable, Gate outcomes with evidence, actual
operation records, output artifacts and their locations. Multiple Runs of the same
Task version remain independent. Creating a record does not execute the Task.

Creation takes `task` (the [complete snapshot](TASK.md)), `original_request`
(nonempty string), `resolved_inputs` (JSON object), and optional `workflow` (any
finite JSON value; omitted means not supplied). These are frozen in the manifest.
There is no AI planner; a supplied workflow is recorded without being executed.

Run IDs are generated lowercase UUID hex strings. Every appended record has a
positive, contiguous sequence number and UTC recording timestamp. Sequence order,
not timestamp comparison, defines the committed order within a Run. Gate attempts,
operational events and artifact registrations share this stream. Rechecks append
new outcomes; all attempts remain inspectable and no latest outcome replaces history.

Read returns the manifest and ordered `records`, plus `gate_outcomes`, `events` and
`artifacts` filtered from that same stream. Paths and digests locate preserved
evidence; the recorder verifies them on read. Outputs only exist if a caller produces
and registers them. Task acceptance and overall Run success are not inferred from
the existence of records or a PASS on some Gate.
