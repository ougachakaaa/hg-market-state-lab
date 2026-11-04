# Equity Index Futures Basis Monitor usage

Start at the [Task entry](ARCHITECTURE.md), then read [task.json](task.json) and the
[query and result contract](authority/QUERY_AND_RESULT.md). This guide is usage-only,
not a competing contract. The [Task catalog](../README.md) is the Workbench entry.

## Status

Task version 1 authority was approved in G1; the original approval evidence is
[DESIGN_REQUEST.md](DESIGN_REQUEST.md). G2 implements the Task-local runtime under
[`runtime/run_monitor.py`](runtime/run_monitor.py) and deterministic tests using fake
public services. The three Gates, three deliverable files and same-Run evidence are
implemented. Live acceptance has **not** been performed: Task approval is not
authorization for Tushare or Calendar access.

An Agent must obtain separate, explicit user authorization that states the intended
family/date scope and the possible external acquisition. Never manufacture that
authorization or treat a synthetic test reference as live approval.

## Agent path

1. From the repository root read `AGENTS.md`, `workbench/AGENTS.md`, then the
   [Task catalog](../README.md).
2. Read this Task's [ARCHITECTURE.md](ARCHITECTURE.md), [task.json](task.json) and
   [authority/QUERY_AND_RESULT.md](authority/QUERY_AND_RESULT.md).
3. Resolve the user's families and dates. Keep the original request verbatim; use
   `IF`/`IH`/`IC`/`IM` (or a documented alias) and absolute dates (or one supported
   relative expression).
4. Obtain separate authorization, then run the command below from the repository root.

## Request file

Explicit inclusive dates:

```json
{
  "original_request": "查询 IF、IH、IC、IM 自 2026-10-20 至 2026-10-31 的年化基差",
  "futures_families": ["IF", "IH", "IC", "IM"],
  "start_date": "2026-10-20",
  "end_date": "2026-10-31"
}
```

Supported relative expression (`最近两周` or `最近 N 个交易日`):

```json
{
  "original_request": "查询 IM 最近两周的年化基差",
  "futures_families": ["IM"],
  "date_expression": "最近两周"
}
```

`anchor_date` may be added only with `date_expression`; it must be a CFFEX open date
not later than the execution date in `Asia/Shanghai`. Do not supply both explicit
dates and a relative expression. No default family, date, N or anchor exists.

## Execute

```powershell
poetry run python workbench/tasks/equity_index_futures_basis_monitor/runtime/run_monitor.py `
  --input workbench/tasks/equity_index_futures_basis_monitor/runtime/request.example.json `
  --authorization-reference "<paste the user's actual authorization>"
```

Four-family example:

```powershell
poetry run python workbench/tasks/equity_index_futures_basis_monitor/runtime/run_monitor.py `
  --input workbench/tasks/equity_index_futures_basis_monitor/runtime/request.four_families.example.json `
  --authorization-reference "<paste the user's actual authorization>"
```

The reference must quote the user's actual message covering the displayed family/date
scope and the possible Tushare/Calendar access. It is not a password or token, and an
Agent must not invent it. A missing reference performs no market access.

Omit `--authorization-reference` to validate and freeze an explicit-date request
without any market access. Acquisition and delivery are then recorded BLOCKED. A
relative expression cannot be resolved without authorization because the CFFEX
calendar anchor must be read.

Optional `--root PATH` selects an existing Run store; the default is
`workbench/.runs/`. Exit codes follow the Gate outcome: `0` PASS, `1` FAIL, `2`
BLOCKED. The command prints one JSON object with the Run ID, Gate outcomes, overall
and coverage status, and artifact references.

## Outputs and evidence

A delivery attempt produces these same-Run artifacts:

```text
resolution.json
acquisition.json          # lossless public results and classified failures
basis_daily.csv           # exact 11 columns, canonical order
result.json
REPORT.md
verification.json
```

The Calendar export is preserved separately. Read the Run with the existing public
operation:

```powershell
poetry run python workbench/run_store.py read --run RUN_ID
```

Files are under `workbench/.runs/RUN_ID/blobs/ARTIFACT_ID`. The `verification.json`
artifact records the CSV/result/report/acquisition checks and artifact digests. Market
data is never committed to Git and is not a Research publication or Dataset.

## Deterministic verification

```powershell
poetry run pytest workbench/tests/test_futures_basis_monitor.py
poetry run ruff check workbench
poetry run mypy workbench/tasks/equity_index_futures_basis_monitor/runtime/run_monitor.py
```

The tests inject fake public product and Calendar services; they do not call Tushare.
Do not modify [task.json](task.json) without a new version and explicit user approval.
