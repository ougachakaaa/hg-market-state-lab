# Equity Index Futures Basis Monitor Task

Task `equity_index_futures_basis_monitor` version 1 is defined by the immutable
[task.json](task.json); its original approval evidence remains
[DESIGN_REQUEST.md](DESIGN_REQUEST.md). Task approval does not authorize live market
access. The shared [Task](../../contracts/TASK.md), [Run](../../contracts/RUN.md),
[Gate](../../contracts/GATE.md) and [storage](../../contracts/STORAGE.md) contracts
apply.

## Purpose and ownership

The Task resolves an explicit CFFEX equity-index futures family set and inclusive date
window, obtains the existing public annualized basis history once per family, and
delivers Run-scoped machine-readable data, a concise report and execution evidence.

The Task owns intent resolution and freezing, per-family orchestration, the required
output and report, coverage reporting, Gate definitions and Run evidence. It does not
own family/underlying/listing facts, contract lifecycle, active-universe selection,
`M0/M1/Q1/Q2` slots, `days_to_delist`, the basis or annualization formulas, Source
scope, product completeness, Dataset storage or Research statistics/publication. Those
remain with:

- [Snapshot capability catalog](../../../data_snapshot/CAPABILITIES.md)
- [CFFEX basis shared authority](../../../data_snapshot/src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md)
- [Product authority](../../../data_snapshot/src/data_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md)
- [Product data and completeness](../../../data_snapshot/src/data_snapshot/products/cffex_equity_index_basis_history/data.md)
- [Product read/application contract](../../../data_snapshot/src/data_snapshot/products/cffex_equity_index_basis_history/read-contract.md)
- [CFFEX Calendar public service](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md)

## Supported families

| Family | Underlying | Explicit aliases |
| --- | --- | --- |
| `IF` | `000300.SH` | 沪深300, 沪深300指数 |
| `IH` | `000016.SH` | 上证50, 上证50指数 |
| `IC` | `000905.SH` | 中证500, 中证500指数 |
| `IM` | `000852.SH` | 中证1000, 中证1000指数 |

This table is a support and resolution reference. Canonical family, underlying and
listing facts remain owned by the shared CFFEX authority and are read from the public
product result; a divergence requires a new Task version.

## Key invariants

1. One family per public product request. The Task calls
   `run_cffex_equity_index_basis_history` once per requested family and does not change
   the product's single-family scope.
2. Market values are copied verbatim from `CFFEXEquityIndexBasisObservation`. The Task
   does not compute a parallel basis, annualization, slot or lifecycle result, and does
   not filter by volume, open interest, main-contract flag or liquidity.
3. The requested window is passed unchanged. The product's effective start (listing
   intersection) and actual observed dates are reported separately; the requested end
   date is never presented as the last observed date.
4. Product success proves a complete panel only on its actual observation dates. It
   does not prove that every expected CFFEX session in the requested window was
   observed.
5. Coverage is `verified_complete`, `verified_partial`, `unverified` or
   `not_applicable`. Expected sessions come from the published CFFEX Calendar. If
   verification is unavailable, no completeness claim is made.
6. A failed family is preserved as an explicit failure. Successful families may still
   be delivered with their data, but the run cannot be complete and `result_delivery`
   cannot PASS.
7. Outputs and evidence are Run artifacts. Market data is never committed to Git and
   is not a Research publication or Dataset.
8. Task approval is not execution authorization. Actual market access needs a
   separate, explicit user authorization.

## Navigation

- [Query and result contract](authority/QUERY_AND_RESULT.md)
- [Usage and current status](README.md)
- [Approval evidence](DESIGN_REQUEST.md)
- [Task catalog](../README.md)
- [Workbench agent entry](../../AGENTS.md)
- [Repository architecture](../../../ARCHITECTURE.md)

## Versioning and status

Task version 1 defines the authority and the G2 implementation contract. The Task-local
runtime at [`runtime/run_monitor.py`](runtime/run_monitor.py) implements that contract:
it freezes resolved inputs, invokes the public basis product once per family, checks
expected CFFEX sessions through the public Calendar service, writes the three required
outputs and records the three Gates with same-Run evidence. Deterministic verification
uses fake public services. Live acceptance requires separate, explicit user
authorization and is not implied by Task approval or by a successful synthetic test.
Any semantic change requires a new version and user approval; existing Run snapshots
remain frozen.
