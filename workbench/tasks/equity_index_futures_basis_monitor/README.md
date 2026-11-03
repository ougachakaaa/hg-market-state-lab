# Equity Index Futures Basis Monitor usage

Start at the [Task entry](ARCHITECTURE.md), then read [task.json](task.json) and the
[query and result contract](authority/QUERY_AND_RESULT.md). The original approval
evidence is [DESIGN_REQUEST.md](DESIGN_REQUEST.md); the [Task catalog](../README.md) is
the Workbench entry. This guide is usage-only, not a competing contract.

## Current status: G1 authority only

Task version 1 currently defines the approved authority and the G2 implementation
contract. There is no runtime script, command, Run, Gate outcome, market request or
generated output under this Task yet.

Do not execute the operation and do not treat Task approval as authorization for
Tushare or Calendar access. G2 execution requires a separate, explicit user
authorization covering both the public product and Calendar data access.

## Agent path

1. From the repository root, read `AGENTS.md`, then `workbench/AGENTS.md`, then the
   [Task catalog](../README.md).
2. Read this Task's [ARCHITECTURE.md](ARCHITECTURE.md), [task.json](task.json) and
   [authority/QUERY_AND_RESULT.md](authority/QUERY_AND_RESULT.md).
3. For design or review, stop at the authority. For G2, obtain separate execution
   authorization before any market request.

## G2 pending

G2 must implement, under a separate authorization:

- input resolution and freezing, including the published CFFEX calendar anchor and
  expected-session coverage;
- one public product call per requested family and lossless acquisition evidence;
- `basis_daily.csv`, `result.json` and `REPORT.md` generation;
- coverage classification (`verified_complete`, `verified_partial`, `unverified`,
  `not_applicable`) and delivery verification;
- RunStore integration, Gate outcomes and read-back verification;
- deterministic tests using fake public product/calendar services, without live
  Tushare access.

The exact contract is [authority/QUERY_AND_RESULT.md](authority/QUERY_AND_RESULT.md).
Do not modify [task.json](task.json) without a new version and user approval.
