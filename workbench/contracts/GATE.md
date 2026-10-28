# Gate contract

A Gate definition and its criteria/order/dependencies belong to a Task. Its outcome
and supporting evidence belong to a Run of that Task. The recorder accepts only
Gate IDs defined in that Run's frozen Task snapshot. Workbench defines no default
Gates and no universal sequence, including no six-Gate Research sequence.

| Status | Meaning | Recording requirement |
| --- | --- | --- |
| `PASS` | Criteria satisfied by an actual check | At least one registered, preserved evidence artifact from the same Run |
| `FAIL` | A check was attempted and did not satisfy criteria | Nonempty reason describing the failed attempt |
| `BLOCKED` | Prerequisites prevent the check | Nonempty reason describing the missing prerequisite |
| `SKIPPED` | Check intentionally omitted | Nonempty explicit reason |

Each outcome records `gate_id`, exact uppercase `status`, `reason` (string, may be
empty only for PASS), and `evidence` (array of same-Run registered artifact IDs).
All statuses may cite evidence. Repeated Gate outcomes append independent attempts.

Evidence is supplied by the executor and copied into immutable Run storage before
an outcome references it. Storage validates existence, ownership and digest. The
agent/executor remains responsible for truthfulness, relevance, actual check execution
and Task ordering/criteria. The recorder cannot establish semantic PASS merely by
hashing arbitrary bytes; it is neither a Gate evaluator nor an approval authority.
