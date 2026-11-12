# Static Example result contract

Specializes [Demo Runtime](ARCHITECTURE.md). This contract owns public Example packaging,
not market semantics, transport schemas, numerical methods or a second business model.
D0 defines requirements; only the V1 Basis fixture currently exists as a Demo artifact.

## Minimum packaging and identity

Each committed Example must identify a versioned Example profile/revision, owning feature
and result profile/definition version, fixed semantic request/observation, synthetic
classification, generator entry and reproducible invocation, and human-readable disclosure
(label, data source, notice). Associate the complete producer result with that identity;
keep a committed content digest or equivalent reproducible check for drift. Metadata may
be an envelope or manifest; exact filenames/JSON field spelling are implementation choices.
Do not hand-edit result payloads or create a new union business DTO across features.

All initial V2 Examples are deterministic Synthetic public facts passed through unchanged
formal producers and result projections. No unauthorized real market data, credentials,
Cookies, private caches/paths or machine runtime metadata may be published. A future
real-data Example needs explicit redistribution authority and a reconciled decision.
Disclosure must distinguish synthetic history/performance from observed markets and actual
trading, and must not claim live availability, server execution or sealed evidence files
that are absent. Labels stay visible or discoverable across page navigation and results.

Dates must be inputs to generation of legal synthetic facts for that window, including
producer-required calendars, contract lifecycle, upstream scope and warm-up. Replacing
dates in old output is forbidden. Preserve requested dates separately from actual observed
coverage; absent sessions/results are not fabricated to fill the target window. Never
calculate Basis, premiums, statistics, slots, PnL or other financial outputs in the browser.

## Required examples and formal validation

| Surface | Target | Producer/result validation boundary |
| --- | --- | --- |
| Historical Basis | IM, inclusive 2026-01-01–2026-11-11; all six report sections | Formal Research producer/reader projection; `validateReportData`, published report profile, Visualization V1/V2 and fixed-request/coverage association |
| MO Option Chain | MO; preferred observation 2026-11-11; fixed close price type | Formal Snapshot product and HTTP projection; generated 200 response schema and existing feature semantic checks; complete response, not selected chart data |
| MO Premium Plane | MO; preferred observation 2026-11-11; fixed close price type | Its own formal Snapshot producer/HTTP projection, not Option Chain DTO; generated 200 schema, nonempty real Points and existing semantic checks; preserve full raw payload |
| Backtesting | Futures Roll Long, IM, inclusive 2026-01-01–2026-11-11; published strategy profile | Formal W2 adapter/Position-Driven Core result and published result projection; generated result schema, profile/definition, request agreement and both V2 Views |
| Research Overview | Published capability list/details plus existing local-case descriptions | Capability GET generated schemas and matching descriptor IDs; no provider/readiness inference |
| Research Explorer | Legal Publication/Analysis and referenced Views, or explicit static empty state | Publication list/manifest/analysis/View generated schemas, identity/reference association and Visualization validation; empty state follows formal empty-list semantics |
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

If the preferred Daily observation cannot be generated legally, record the actual fixed
observation and reason with producer validation evidence; do not silently substitute or
claim 2026-11-11. Research and Backtesting target windows remain required; inability to
produce them is an implementation gap, not permission to relabel V1.

Explorer may initially use the formal empty-list state with an explicit “static Example;
no embedded Publication” explanation. It must not claim that a live Store was checked.
If records are included, all selected manifests/analyses/Views must resolve from the
committed set and preserve published ordering, null/zero, status, coverage and provenance.
Selections and bundled pagination are local display; Refresh and server retries are absent.

## Verification and updates

Every Example passes the current formal result contract before rendering; invalid,
unsupported or identity-mismatched data shows a static error and no result. CI validates
all committed Examples against current contracts, including semantic associations and
Views, not just TypeScript casts or envelope metadata. Existing `contract:check` continues
to own backend/OpenAPI/generated-type freshness; [contract authority](../../contracts.md)
defines its relationship to the additional Demo check.

Provide deterministic regeneration or verification commands without network/credentials,
and review output diffs before committing. Full producer reproduction may run explicitly
or in dedicated CI; release only validates/consumes the committed outputs. Synthetic
input generation must remain outside business modules' stable product semantics: no
parallel DataLake, Research or Backtesting Demo product/case/strategy authority.

V1 remains pinned by [its existing fixture authority](futures_basis/ARCHITECTURE.md),
`futures_basis_demo_fixture_v1` / `report.v1.json` and generator `--check`. Its 44-session
2024 window is not the V2 target. Generate a new revision for the new window; preserve
old evidence and never silently rewrite V1 profile meaning.
