# Local state after the module migration

This is an operator guide, not a cache schema migration. Canonical module identities belong to [repository architecture](ARCHITECTURE.md#naming-and-transition-authority). Stop all writers, CLI jobs and servers before switching a checkout; do not run `ensure` to test whether old data survived.

Git relocates tracked files only. Existing ignored assets must be copied separately:

| Old location | Canonical location |
| --- | --- |
| `data-lake/datasets/<id>/data/` | `data_lake/datasets/<id>/data/` |
| `data-lake/data/` (legacy, still isolated) | `data_lake/data/` (still isolated, never adopted by services) |
| `market-snapshot/.env` | `data_snapshot/.env` |
| `market-snapshot/data/` | `data_snapshot/data/` (Raw and snapshots keep internal layout) |
| `market-research/observations/<id>/data/` and `output/` | Same relative paths under `market_research/observations/` |
| `market-research/output/` | `market_research/output/` |

Absolute Research output locations outside the repository stay unchanged. Review any locally customized output paths in `market_research/research.toml`, shell variables, IDE tasks and external scripts; map only module prefixes. Snapshot product IDs, filenames and SQLite schemas are unchanged. Copy complete SQLite directories, including WAL/journal companions, after stopping writers. Keep an independent backup outside the checkout.

From repository root, using Python 3.13:

```powershell
python .codex/scripts/migrate_local_state.py
python .codex/scripts/migrate_local_state.py --apply
```

The default command reports counts without reading credentials into console output. `--apply` copies only the listed assets, creates files exclusively, accepts identical existing files and refuses conflicting destinations or symlinks. It verifies SHA-256 for every file; it never deletes sources, merges conflicting files, rewrites SQLite or contacts a Source. If interrupted, stop and inspect; a repeat accepts already verified identical files. Resolve conflicts explicitly from backups rather than replacing either copy automatically.

After all files verify, move the remaining old asset directories (and old `.env`) to an explicitly chosen backup directory **outside this checkout**, using native filesystem tools with non-existing destinations. Keep that backup until validation is complete. Run the default command again: it must report zero legacy files. Runtime path checks refuse remaining legacy owned state, even if a new destination also exists, so a partial copy cannot silently trigger collection against a new empty cache. The isolated historical `data_lake/data/` is never adopted or rebuilt by this procedure.

A whole-directory rename carries ignored state in the implementation checkout; Git updates in other checkouts still require the procedure above. No assets or hash manifest belong in Git.

Keep the root `.venv`; reinstall from root with `poetry install` to refresh editable source roots and the `lab = ui_cli.cli:main` console entry. Old module-local environments are inactive historical installations: do not copy or activate them. `ui_web/node_modules` is worktree-local; run `npm install` in `ui_web` (or `npm ci` for a clean dependency installation). Do not copy old `web-ui/node_modules` or build output. Old ignored installation directories can remain until explicitly cleaned by their owner. The root `.worktreeinclude` now copies `data_snapshot/.env`; migrate the source checkout before creating managed worktrees.

Verify `poetry run lab doctor`, `lab datalake list`, `lab research list`, installed imports from a repository-external cwd, and the tests in [DEVELOPMENT.md](DEVELOPMENT.md) / local AGENTS. Verify copied assets by the helper's hashes and operator-selected read-only inspection; do not use live acquisition, cache rebuild or a schema upgrade as migration validation. Existing cache compatibility/rebuild rules in [DataLake persistence](data_lake/PERSISTENCE.md) remain unchanged.
