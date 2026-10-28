# WB-01 delivery and reconciliation

Verified on 2026-10-28 against `develop` at
`2fd3aec609e04851c65075204e4fb7cf5839900e` using root Poetry / Python 3.13.11.
`main`, local `develop` and `origin/develop` initially pointed to that same commit;
work was performed on `develop`. This document records delivery evidence, not new
Task or storage semantics.

## Authority topology and ownership

```text
root AGENTS.md / ARCHITECTURE.md / README.md
    -> workbench/AGENTS.md                 agent execution entry
    -> workbench/ARCHITECTURE.md           identity, ownership, boundary/navigation
        -> contracts/TASK.md              Task definition, version, user approval
        -> contracts/RUN.md               per-execution identity and evidence
        -> contracts/GATE.md              Task check / Run outcome distinction
        -> contracts/STORAGE.md           shared local storage and publication
    -> workbench/README.md                 practical usage
```

Task owns goal/scope, inputs, allowed capabilities, planning constraints, expected
outputs/acceptance and its own Gate definitions/dependencies. User approval, not agent
proposal or recorded success, promotes business Task authority. Run owns the frozen
Task snapshot, resolved inputs, original request, optional supplied workflow and all
execution records. Gate definitions remain on Task; PASS / FAIL / BLOCKED / SKIPPED
outcomes and evidence remain on Run. No default Gate sequence or business Task exists.

The root provides navigation only. Specialized schemas and persistence semantics
reside in the four narrow contracts; Workbench is outside the module taxonomy and
inherits the single root Python runtime without granting business import permission.

## Changed files and public storage

Created `workbench/AGENTS.md`, `ARCHITECTURE.md`, `README.md`, `ACCEPTANCE.md`,
`contracts/TASK.md`, `contracts/RUN.md`, `contracts/GATE.md`, `contracts/STORAGE.md`,
`run_store.py`, `tests/support.py`, `tests/test_run_store.py` and
`tests/acceptance_example.py` (all paths in this sentence relative to `workbench/`).
Changed root `AGENTS.md`, `ARCHITECTURE.md` and `README.md` for minimal navigation;
`.gitignore` excludes `/workbench/.runs/`; `pyproject.toml` adds only test discovery.
The existing first test path remains `ui_cli/tests`.

Public invocation is `poetry run python workbench/run_store.py` with `create`,
`artifact`, `gate`, `event` or `read`; requests are UTF-8 JSON files passed with
`--input`, and existing Runs use `--run`. See [usage and complete examples](README.md).
An optional `--root` precedes the operation. Default output is:

```text
workbench/.runs/<run_id>/manifest.json
workbench/.runs/<run_id>/records/<sequence>.json
workbench/.runs/<run_id>/blobs/<artifact_id>
```

The manifest preserves Task identity/version, snapshot and SHA-256. Artifact records
retain original locations, preserved local paths, SHA-256 and byte size. Atomic
exclusive publication prevents replacement, and a Run writer lock prevents concurrent
record sequence collisions. Read validates stored state and returns ordered histories.

## Executed verification

```text
poetry run pytest workbench/tests ui_cli/tests data_lake/tests/test_boundary.py market_statistics/tests/test_statistics_architecture.py ui_http/tests/test_architecture.py -q
126 passed in 8.91s

poetry run ruff check workbench
All checks passed!

poetry run mypy workbench/run_store.py
Success: no issues found in 1 source file

poetry run python workbench/tests/acceptance_example.py
Completed with two distinct Runs and all round-trip assertions satisfied.

git diff --check
Passed.
```

The final combined suite includes 39 Workbench checks, with no skips. It exercises
all script operations, Task/version isolation, all Gate statuses and reasons,
same-Run evidence enforcement, append-only rechecks, preserved artifacts, ordered
events, collision refusal, injected publication failure, a concurrent writer and
read-before-publication, corruption rejection, traversal and symlink/junction refusal.
On this Windows account, the alias test uses a directory junction because ordinary
symlink creation lacks privilege. The other 87 checks cover existing CLI and module
architecture boundaries; no live market acquisition or business workflow was executed.

An initial regression run found the existing CLI test requires `ui_cli/tests` to be
the first discovery path. Reordering the new Workbench test path to the end resolved
that integration issue without changing the existing test or module implementation.

## One synthetic Task, two actual local Runs

Task: `synthetic-file-check`, version `1`, approval kind `synthetic` (test-only).
Both manifests preserve the identical Task snapshot with SHA-256:

```text
b9f1a427cff11a946137a92727cb0b62ff7c5cb33bdd4519a716a2730d68bdc8
```

| Run ID | Gate outcomes | Record sequences |
| --- | --- | --- |
| `370e40c1722046ddae619a7cf822e579` | inspect PASS, optional FAIL | 1, 2, 3, 4 |
| `ca8d0814ebd7481797f0c505cef8c455` | inspect BLOCKED, optional SKIPPED | 1, 2, 3, 4 |

Run 1 actually reads the expected text and attempts a deliberately mismatched optional
comparison. Run 2 has its inspection prerequisite disabled and intentionally omits
the dependent optional check. These are synthetic evidence-storage scenarios, not a
global Gate sequence or an approved business Task.

The Runs are under ignored `workbench/.runs/<run_id>/`. Their registered preserved
outputs are respectively `blobs/fff698b6b6e94cb7a52fe205bf0461d4` and
`blobs/ceeca5cd213449d2825a6faf25316542`, each containing `synthetic evidence`, SHA-256
`48736e58b409ed0241c8d7bed9dc188a59e13002f48e7492850bec15b59147b6`.
Both source files were removed with their temporary input directory before the final
read-back. Records, identity, snapshot and artifacts remained retrievable. The caller's
Task definition remained unchanged and contains no Run outcomes.

Local ignored evidence is disposable and not included in a fresh checkout. Rerun the
example to reproduce the same assertions with new Run/artifact identities.

## Scope reconciliation and limits

No WB-01 contract gap remains. Explicit limits are recorded in
[storage authority](contracts/STORAGE.md): local regular-file artifacts, a filesystem
supporting hard links, explicit busy errors and manual stale-lock recovery after a
crashed writer. Storage records supplied approval provenance and evidence; it does
not authenticate approval, judge evidence relevance or execute Task/Gate dependencies.
Future Task catalogs, approval verification, remote retention and finalization remain
future decisions, outside this foundation.

No files under `data_lake`, `data_snapshot`, `market_research`, `market_statistics`,
`market_modeling`, `ui_cli`, `ui_http` or `ui_web` changed. No existing market runtime
data was used as test output or modified. No package, dependency, lockfile, environment,
`lab` command group, server, database, planner, scheduler or orchestration was added.
