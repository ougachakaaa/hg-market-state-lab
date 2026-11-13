# Static Example result contract

Specializes [Demo Runtime](ARCHITECTURE.md). This contract owns private development and reviewed public Example packaging,
not market semantics, transport schemas, numerical methods or a second business model.
D3-R0 replaces D0's synthetic V2 policy. V1 remains a historical compatibility artifact.

## Minimum packaging and identity

All formal V2 market quotations, financial statistics, research reports and backtest
performance must be `real_market`: genuine historical inputs processed by unchanged
formal producers. Synthetic / Artificial / Mock Market Facts are test-only, never formal
V2 Examples. Static delivery does not imply synthetic origin. Retiming old synthetic
outputs, interpolation, extrapolation, zero filling and cross-date substitution to fake
market coverage are forbidden. Never compute financial results in the browser.

Each Example identifies its versioned packaging profile/revision, owning feature, fixed
semantic request/observation and the provenance, producer, integrity, disclosure and rights
records required by [Authenticity and rights](AUTHENTICITY.md). Metadata may be an envelope
or manifest; it must not redefine business DTOs or financial methods. Results are never
hand-edited. Acquisition and producer execution are explicit development operations;
release does not acquire or regenerate data. Private local packaging is permitted before
public rights clearance; only reviewed public-safe Examples may be committed or deployed.

## Temporal semantics

Private D3-R2 packaging uses explicit external `--output` and `--r1` paths.
`ui_web/scripts/private_mo_examples.py acquire` calls the two independent public
Product Services with a real configured Source; `verify` is credential-free and
never reacquires. Results are exact official HTTP projections, separate from the
versioned Demo manifest. SHA-256 inventories bind each Product's own retained Raw,
Source call timestamps, result and R1 comparison evidence; these are Demo provenance
digests, not Product-owned input fingerprints. A detached manifest digest detects
accidental manifest edits. Verification uses official Python DTOs and existing
TypeScript feature validators, and checks retained identity/price/reference coverage
without implementing financial formulas. Full financial replay requires the public
Service against a Source: no pure offline service replay is currently published.
Neither operation admits data to public builds or clears redistribution rights.

The common inclusive research window is `2026-01-01..2026-11-11`. Requested Window and
Actual Observed Coverage are separate: retain actual sessions, missing observations and
producer completeness semantics. Do not replace coverage with request endpoints. No
fictional quotations are generated on non-trading days. Producer-required preparation
outside the window must record dates, purpose, source and input fingerprint separately;
it must not appear as unexplained in-window display facts. Missing data never authorizes
synthetic fallback or a second financial calculation policy.

## Required examples and formal validation

| Surface | Target | Producer/result validation boundary |
| --- | --- | --- |
| Historical Basis | IM, inclusive 2026-01-01–2026-11-11; all six report sections | Formal Research producer/reader projection; `validateReportData`, published report profile, Visualization V1/V2 and fixed-request/coverage association |
| MO Option Chain | MO; required observation 2026-11-11; fixed close price type | Formal Snapshot product and HTTP projection; generated 200 response schema and existing feature semantic checks; complete response, not selected chart data |
| MO Premium Plane | MO; required observation 2026-11-11; fixed close price type | Its own formal Snapshot producer/HTTP projection, not Option Chain DTO; generated 200 schema, nonempty real Points and existing semantic checks; preserve full raw payload |
| Backtesting | Futures Roll Long, IM, inclusive 2026-01-01–2026-11-11; published strategy profile | Formal W2 adapter/Position-Driven Core result and published result projection; generated result schema, profile/definition, request agreement and both V2 Views |
| Research Overview | Genuine published capability list/details plus existing local-case descriptions; no invented historical dates | Capability GET generated schemas and matching descriptor IDs; no provider/readiness inference |
| Research Explorer | Real-input Publication/Analysis with observed scope within 2026-01-01..2026-11-11, and referenced Views | Publication list/manifest/analysis/View generated schemas, identity/reference association and Visualization validation; empty state follows formal empty-list semantics |
| Daily Data overview | Existing links and descriptions | No new financial fixture; route coverage still required |

The [feature catalog](../../FEATURES.md) leads to each formal producer and HTTP contract.
Generation must use their existing public boundaries and formal projection/validation,
not handwritten financial outputs or invented successful HTTP/Run envelopes. Extract
reusable pure validators where current APIs combine validation and transport. Committed
HTTP-shaped product bodies retain the published wire shape, but are labelled static
Examples, not responses received by the browser. Static result rendering does not require
forging an accepted/completed Run to satisfy a production lifecycle hook.

Basis must retain Overview, Historical Basis, Distributions, Term Structure, Discount
Persistence, Evidence and Limitations. Backtesting reuses only current Summary, Returns,
Drawdown, Trades, Rolls and Evidence/Limitation support; no extra metrics, export or
business computation model is authorized. An online-only evidence sentence must become
origin-aware in the shared presentation, without duplicating financial sections.

If either Daily source is unavailable for 2026-11-11 close, record FAIL for proven
nonconformance or BLOCKED for unresolved availability, with evidence. Do not use another
date, price type or synthetic data. Research and Backtesting retain their full requested
windows; inability to produce them is a gap, never permission to relabel V1.

Explorer may initially use the formal empty-list state with an explicit “static Example;
no embedded Publication” explanation. This is a delivery gap, not R5 completion. It must not claim that a live Store was checked.
If records are included, all selected manifests/analyses/Views must resolve from the
loaded, validated set and preserve published ordering, null/zero, status, coverage and provenance.
Selections and bundled pagination are local display; Refresh and server retries are absent.

## Verification and updates

Every Example passes the current formal result contract before rendering; invalid,
unsupported or identity-mismatched data shows a static error and no result. CI validates
all committed Examples against current contracts, including semantic associations and
Views, not just TypeScript casts or envelope metadata. Existing `contract:check` continues
to own backend/OpenAPI/generated-type freshness; [contract authority](../../contracts.md)
defines its relationship to the additional Demo check.

Provide offline, credential-free integrity and contract verification of retained inputs
and outputs. Producer replay uses legally retained private inputs and a recorded invocation,
source revision, toolchain and definition versions; live reacquisition is a separate action
and is not assumed byte-identical. Review diffs and public rights before committing any
result. Public CI verifies only rights-cleared material; private reproduction must not upload
restricted inputs or diagnostics. No parallel Demo business product/case/strategy is created.

V1 remains pinned by [its existing fixture authority](futures_basis/ARCHITECTURE.md),
`futures_basis_demo_fixture_v1` / `report.v1.json` and generator `--check`. Its 44-session
2024 window is not the V2 target. Create separate real-market V2 packaging; preserve old evidence, window and results. Never
relabel V1 as real_market or repackage it as a V2 Example. D7 public V2 excludes historical
synthetic Examples from its entry, reachable assets and deployment package.
