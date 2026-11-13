# Static Demo V2 runtime authority

Specializes [module ownership](../../ARCHITECTURE.md), [application](../../application.md),
[workspace navigation](../../workspace.md) and [presentation boundaries](../../presentation-architecture.md).
This is the canonical Demo Runtime entry, not a business module, second Web product,
Mock Backend or new financial capability. D0 established the shared architecture; D1/D2 implemented shell/presentation boundaries.
D3-R0 supersedes only the synthetic V2 source decision; full V2 remains unaccepted.

## Identity and ownership

**Static Demo V2 = Shared Production UI + Embedded Example Results + Anonymous Read-Only Runtime.**

Production Web is the sole owner of business page presentation. Both compositions use
its application shell, sidebar/navigation/breadcrumb, feature page presentation, result
components, charts/tables, feature visualization and applicable pure local presentation
state. UI/layout/theme/chart changes propagate by shared code. No parallel Demo business
pages, copied JSX or duplicated projections may be maintained. Demo entry, composition
and fixture loader may be separate; they own no business display logic.

The application selects runtime composition, never financial semantics:

| Concern | Production Runtime | Static Demo Runtime |
| --- | --- | --- |
| Entry | Existing Authentication Gate | Anonymous entry, explicit static historical real-market disclosure |
| Data/control | Real HTTP queries, preflight, Run lifecycle | Validated embedded Examples and local selection only |
| Execution | Owning Python Research/Backtesting and normal business reads/writes | No backend, database, Token or Python runtime |
| Presentation | Canonical feature presentation | The same feature presentation with fixed request and read-only capability |
| Routing | Existing pathname/history, server `run_id` query semantics | Hash routing below `/hg-market-state-lab/` |

Composition supplies route/navigation, header identity/actions and feature public
entries to shared shell presentation. Production Auth stays outside that presentation;
Demo must neither mount nor import its gate, Auth hook/client or production controllers.
Features separate production data/execution controllers from shared presentation and
static Example controllers. The static controller supplies validated data and local
presentation state, not an HTTP-shaped execution service. Pure validators may be extracted
from API modules without changing contract ownership. Type-only generated contract imports
are allowed; HTTP request implementations, polling and preflight are not static dependencies.

Isolation requires both a clean static dependency graph and absence of business network
activity, not just disabled controls or tree-shaking an imported production App. Do not
introduce a generic Mock HTTP Server, plugin system or unnecessary DI framework.

## Complete navigation and routing

Demo must cover every current formal business route, including both overviews:

| Route identity | Shared surface / Example source |
| --- | --- |
| `/research` | Research Overview; committed capability descriptions and existing local-case summaries |
| `/research/futures-basis` | Historical Basis; full six-section Example report |
| `/research/publications` | Research Explorer; Publication/Analysis Example or explicit static empty state |
| `/data` | Existing Daily Data overview and both product links |
| `/data/mo-option-chain` | MO Option Chain Example |
| `/data/mo-premium-plane` | MO Premium Plane Example |
| `/backtesting` | Futures Roll Long Example |

Research Explorer becomes an explicit Research Sidebar leaf in **both** runtimes;
its overview link remains. It is a secondary technical reader, not an execution page.
Selection, collapsed navigation and breadcrumb follow the same route identity.

Use `https://<pages-host>/hg-market-state-lab/#/research` and analogous hashes for all
seven surfaces. Root/unknown hash normalizes to `#/research`. Shared navigation must
produce runtime-correct hrefs, including breadcrumbs, rather than absolute production
paths that escape the Pages base. Hash updates, Back/Forward and direct reload preserve
the selected surface; assets remain below the configured base. Report section anchors
must coexist with route hashes without replacing the active route (local scroll or an
explicit fragment encoding is an implementation choice). Demo ignores production `run_id`
inputs and must not restore/contact a server Run. Production retains its existing URLs,
authenticated deep links and `/api` gateway semantics unchanged.

## Read-only capability

The following controls have no callable business action in Demo, including on mount,
keyboard submit, URL changes, retries or direct invocation: arbitrary date/parameter
queries, refetch, Research Submit, Backtesting Submit, Preflight/Refresh, server mutation
and every other backend-dependent action. Display the fixed Example request parameters;
they cannot be edited or submitted. Production controllers must not be mounted behind
disabled buttons. Presentation may hide execution-only controls or show an unavailable
explanation; it may not fake PENDING/RUNNING/COMPLETED, readiness, workers, server Run IDs,
server availability or successful online responses. Local fixture loading/validation
and failure are explicitly static states, not a Run lifecycle.

Preserve pages/Tabs/report sections, Plotly Hover/Zoom/Pan/Reset, tables, local metric,
Slot, expiry, color and viewport selections, and existing local Copy/Export where the
formal feature supports them. These operate only on loaded facts, never recompute
financial results or expand Example query scope. Embedded Explorer selections may read
already bundled records; they are not queries to an API. Do not add export to Backtesting
merely for Demo. Disclosure and Example origin remain clear during reading and downloads;
[Copy/Export authority](../../data-copy-export.md) owns unchanged data formats.

## Examples and maintenance

[Example contract](EXAMPLES.md) owns real-market targets and result packaging;
[Authenticity and rights](AUTHENTICITY.md) owns provenance, independent gates and public admission;
[implementation handoff](IMPLEMENTATION.md) owns current D3-R0 cutover, D3-R1-R6, bounded D1–D6 work
and D7 release handoff. Feature and producer contracts continue to own results.

**Production UI Changes Propagate by Shared Code; Data Contract Changes Are Reconciled by CI.**

Routine UI changes must not require a second page implementation. Additional maintenance
is expected for new formal pages, incompatible result contracts or insufficient Examples.
CI must compare Demo coverage against the canonical production route inventory (not a
second handwritten list) and fail on a missing page. Fixture shape/profile/identity/View
drift must fail CI; stale fixtures must not silently be accepted or regenerated at deploy.

## Generation versus release

Real-data acquisition and result generation/update are explicit development operations using
formal producers in the repository-root environment. Development First permits lawful
acquisition, research, private results and local shared-UI integration while public rights
remain unresolved. Private assets stay outside Git tracking and public build paths. Only
rights-cleared results may enter committed public Examples. Valid, compatible Examples
need not be regenerated for each release. The static runtime itself never acquires data.

Static release consumes only committed Examples and locked npm dependencies. No Python
Research/Backtesting execution, external market-data access, backend, database, token or
fixture regeneration belongs in the release build. Record source commit, dependency lock,
Example versions/digests, build toolchain and resulting artifact/deployment identity;
build results must be deterministic for those inputs. Required CI contract/provenance
verification may use the root Python toolchain in a separate validation job; it must not
turn deployment into fixture generation or live data acquisition.

Long-term release flow is **Feature Development → develop → Release Review → main →
GitHub Actions → GitHub Pages**. Daily develop commits validate compatibility but do not
update the public Demo. Only explicitly reviewed releases to main trigger official Pages
publication. CI gates Production/Demo compatibility before release. A failed build or
deployment never establishes that Live Demo updated; successful deployment and public
HTTP/browser acceptance are separate evidence.

D3-R0 does not change workflow triggers: [current workflow](../../../.github/workflows/deploy-demo-pages.yml)
still deploys the V1 feature branch. D7 owns switching to main and enforcing this release
model. The old V1 WP5 eventual-trigger plan is superseded by D7. Do not push merely to
validate documentation: the existing branch trigger can publish V1.

## Transition and evidence

[Futures Basis V1](futures_basis/ARCHITECTURE.md) retains its committed 2024 fixture
contract, generator and WP3/WP4 historical evidence. Its one-page/no-router and independent
shell describe V1 implementation only; they do not constrain the V2 target. V2 must share
the full formal UI and cannot claim seven-page coverage until implemented and verified.
No historical acceptance is evidence of V2 isolation, new Examples or main-driven release.

D7 requires an independent Publication Review of the exact public artifact, all six
[authenticity and rights gates](AUTHENTICITY.md) PASS, and exclusion of historical V1
synthetic Examples. Attribution alone is not redistribution permission. Local technical
acceptance and public release approval are separate outcomes.

## Explicit private composition (WP-B)

The independent [private build contract](PRIVATE_BUILD.md) owns verified external
input admission, safe static projection injection, origin disclosure and external
output isolation. It does not change the V1 public build or Pages deployment.
