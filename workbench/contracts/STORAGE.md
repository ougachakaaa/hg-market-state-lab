# Shared local storage contract (format 1)

`run_store.py` uses only the standard library and the existing root runtime. Public
operations are `create`, `gate`, `event`, `artifact`, `read`; see [usage](../README.md).
Default store is `workbench/.runs/`, resolved relative to the script, independent of
cwd and ignored by Git. An explicit `--root` may redirect to disposable test or
operator-owned storage; it never redirects business runtime data automatically.

```text
workbench/.runs/<run_id>/
    manifest.json                 # format_version, run_id, created_at, request,
                                  # frozen task, task_sha256, inputs, workflow
    records/00000001.json          # sequence, recorded_at, kind, payload
    records/00000002.json
    blobs/<artifact_id>            # preserved file bytes, SHA-256 verified
    .writer/                      # transient exclusive writer lock
```

`create` consumes the Run creation object. `gate` consumes the Gate outcome object.
`event` consumes `{operation: nonempty string, details: JSON object}` to record actual
operations/results supplied by the caller. `artifact` consumes `{label: nonempty
string, path: local file path}`; relative paths resolve from invocation cwd. It
copies bytes and records generated `artifact_id`, label, absolute `source_location`,
Run-relative `stored_path`, `sha256`, and `size_bytes`. The returned registration
can be used as Gate evidence. The preserved copy remains locatable if the source
changes or disappears. URI-only artifacts and directories are not supported by this
storage contract.

All writes publish a completely written, flushed/fsynced temporary file via an
exclusive hard link, then remove the temporary name. Publication never replaces an
existing destination; local storage must support hard links. Writers serialize per
Run with an exclusive directory lock; concurrent writers receive an explicit busy
error and may retry. There is no scheduler or automatic retry. New Run directories
use exclusive creation. Run IDs and internal paths are constrained, and read checks
path containment (including symlinks), format, identity, sequence, snapshot digest,
record payloads, same-Run evidence references and blob digests. Reads are read-only
and return the committed prefix observed when listing records.

There is no edit/delete/overwrite operation. A failed publication may leave an
unreferenced blob or temporary file, or an incomplete Run directory if initial
manifest publication failed. These are not committed evidence; read fails explicitly
if a manifest is missing or committed content is inconsistent. A crash while holding
`.writer/` leaves a busy Run. After confirming no writer remains, an operator may
remove only that stale lock; the recorder never guesses or deletes evidence to recover.
Atomic visibility is provided; power-loss recovery/directory fsync, hostile-writer
protection, cryptographic authenticity and distributed/network filesystem guarantees
are outside this storage contract. Hashes detect corruption, not malicious coordinated
rewriting.

Invalid requests raise `ValueError`; inconsistent stored content raises `ValueError`;
busy/collision/unsupported-filesystem/I/O failures remain explicit OS errors. Script
CLI prints errors to stderr, exits 1, and prints one JSON result on success (exit 0).
Argparse usage errors exit 2. No operation executes business capabilities, evaluates
Gates, approves Tasks, or mutates a Task file. Future Task catalogs/approval provenance
verification, external artifact retention and Run finalization require separate decisions.
