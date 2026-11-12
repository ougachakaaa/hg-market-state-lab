# Research Catalog & Workspace authority

This read-only frontend slice owns the topic-oriented Research Overview and discovery at `/research`. Research
owns case and capability semantics; [Research capability publication](../../../../market_research/descriptive/RESEARCH_CAPABILITY.md)
and the [HTTP contract](../../../../ui_http/products/research/http-contract.md) own the
online descriptor. This slice consumes only the two Capability GET operations through
its generated OpenAPI contract. It does not preview, execute, probe market availability,
or create Research results.

The catalog distinguishes independently evidenced states:

- `trailing_cumulative_return_v1`: admitted descriptor available through authenticated
  HTTP discovery. `supported` means implementation support; `live_readiness` is shown
  unchanged and is not an execution or provider-readiness claim. Selecting it requests
  the published detail by ID.
- `price_segmentation_v1`: implemented independent Python observation API, with no
  Capability Publication, HTTP consumer, or online execution UI. Its identity and scope
  come from [case authority](../../../../market_research/descriptive/cases/price_segmentation/ARCHITECTURE.md).
- `futures_basis_v1`: implemented local Python case and offline report generation and
  standalone reading workflow, owned by [R01-A](../../../../market_research/descriptive/cases/futures_basis/ARCHITECTURE.md)
  and its [delivery](../../../../market_research/descriptive/cases/futures_basis/DELIVERY.md).
  Its independent online Web Consumer is available at `/research/futures-basis`.
  Selecting the case offers navigation to that sibling page, not execution inside
  this catalog. Offline generation remains independent; provider/cache readiness
  is not established by the existence of an online consumer.

Local descriptions are bounded presentation summaries of those published contracts,
with explicit Python or operator entry instructions. They are not a second backend DTO,
case registry, or assertion of live data availability. No report link is shown without
an actual served report URL. The Research Results action navigates to the existing
`/research/publications` Explorer, which remains the only online Publication reader.

List and selected detail have independent loading, empty, error, and manual retry states.
Changing selection or unmounting invalidates obsolete responses. The application auth
boundary handles 401 and unmounts all Research content; no data survives a session
change. The slice follows the [presentation architecture](../../../presentation-architecture.md)
and [UI system](../../../ui-system.md) without a shared Research runtime or financial
calculation in React.

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using [validated committed Examples](../../demo/EXAMPLES.md), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages.

D2-C implements this boundary. `presentation.ts` exposes the feature-owned `ResearchOverviewPresentation`, pure generated-contract validators (`validateCapabilityList`, `validateCapabilityDetail`, `validateEmbeddedCatalog`) and a feature-local `useStaticCatalog` controller. Production `useCatalog` retains mount list GET, selection-triggered detail GET, independent list/detail retry, cancellation plus request-token stale isolation, protected Auth and HTTP error mapping; `ResearchWorkspacePage` is a thin composition root. Static composition validates the embedded list/detail set, rejects duplicate or unassociated capability identities, selects locally without a GET, and never fabricates a missing detail result. Both runtimes use the same page JSX and feature components. Static origin labels distinguish embedded descriptions from authenticated discovery while preserving published `status` and `live_readiness`. Explorer and Futures Basis navigation remain injected runtime-specific callbacks. `testing/static/` is a verification harness using regression data, not an official D3 Example or public Demo entry.
