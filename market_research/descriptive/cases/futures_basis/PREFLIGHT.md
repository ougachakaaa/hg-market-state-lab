# Futures Basis input preflight

This specializes [the case](ARCHITECTURE.md), [online application](ONLINE_APPLICATION.md)
and [public inputs](INPUTS.md). Research owns this case-specific read-only input
assessment; [HTTP](../../../../ui_http/products/futures_basis_research/http-contract.md)
owns delivery and [Web](../../../../ui_web/src/features/futures_basis_research/ARCHITECTURE.md)
owns interaction. It is not a generic validation framework or a Run state.

## Request validation (L1)

`validate_online_request` reuses `validate_request` and adds the online-only 1,096
inclusive calendar-day limit. Product, date types, order and the Asia/Shanghai
future-date rule are validated before service creation or I/O. Offline bounds do
not change. Today is a legal request date; no close/publication-time rule exists.
Preflight and Run submission share this validator; Run requires no preflight ticket.
L1 raises `RequestValidationError` (ValueError subclass) with fixed safe text and
an optional input-field param; Preflight HTTP projects this as a field-level 400.
Existing Run submission error projection remains unchanged.

## Readiness assessment (L2)

The case public facade publishes `preflight_inputs(FuturesBasisRequest)` and typed
`FuturesBasisPreflight` / `PreflightDependency` results. Optional public services and
an aware clock permit deterministic tests. Production uses public Dataset factories.
No ensure, Source access, market Export, statistics, Run creation, persistence or
execution permit is allowed. Read-only factories require no credentials.

For each window export/validate CFFEX and SSE calendars with existing Export
validation, then query Futures coverage against CFFEX and Index coverage against
SSE. Only complete legal calendars establish target counts. Incomplete legal
calendars make the corresponding downstream `unknown`, with null coverage and no
downstream call. Operation errors and malformed returned evidence stay distinct.
Validate Coverage non-bool nonnegative counters, target count, accounting and the
complete formula. Do not parse exception text to infer a more specific cause.

When end_date is the observed Shanghai market date, also assess the single-day
window. Reuse the assessment when the full window is exactly today. Return all
four dependencies for each applicable scope (`window`, `today`). Separate calls
are not a common snapshot. Coverage is cache completeness, not freshness, upstream
publication evidence, full market-payload validation or a success guarantee.

Dependency states are `complete`, `needs_fetch`, `unknown`, `operation_error`,
`contract_error`. Safe reason codes are respectively null, `cache_incomplete`,
`prerequisite_incomplete`, `operation_failed`, `invalid_evidence`; blocked upstream
errors use `prerequisite_unavailable` for the downstream unknown. Missing, pending
and failed units are all needs_fetch, never proof of Source unavailability. No
per-day identities are inferred from aggregate coverage.

## Web submission policy

`today_gate` is `not_applicable` for history; otherwise `ready` if all four today
dependencies are complete, `unknown` if any is unknown/error, else `not_ready`.
Complete calendars proving closure and zero market targets count as ready.
Today Index coverage must be complete for this Web gate even though formal
preparation continues to allow a legal partial Index Export.

`submission` is `blocked` if any actual check has operation/contract error or the
today gate is not_ready/unknown; otherwise `confirm_required` if any window
dependency is not complete; otherwise `allowed`. Historical calendar cache gaps
are confirmable unknowns. Today gaps must say “本地当日数据未就绪，请先完成数据准备，再重新检查。”;
never claim the upstream has not updated. First use of a cold today cache can be
blocked until a separate existing preparation workflow populates it. No preparation
action is added here. The Run API repeats L1 only; its existing final preparation,
completeness, lifecycle and failure categories remain authoritative and unchanged.

Results carry immutable request identity, UTC checked_at, Shanghai market_date,
submission, today_gate and dependency assessments with optional public Coverage.
No ticket, fingerprint or retained final-input proof is produced. Logs retain a
server-generated correlation ID, dependency/scope/operation, exception type,
coverage and duration; only fixed safe messages enter the public result.

## Runtime acceptance

Synthetic Linux implementation and verification are recorded in
[Preflight acceptance](PREFLIGHT_ACCEPTANCE.md); human usage is in [Usage](USAGE.md).
