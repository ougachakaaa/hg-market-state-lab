# Research Catalog & Workspace authority

This read-only frontend slice owns the topic-oriented Research Overview and discovery at `/research`. Research
owns case and capability semantics; [Research capability publication](../../../../market_research/descriptive/RESEARCH_CAPABILITY.md)
and the [HTTP contract](../../../../ui_http/products/research/http-contract.md) own the
online descriptor. This slice consumes only the two Capability GET operations through
its generated OpenAPI contract. It does not preview, execute, probe market availability,
or create Research results.

## Research Study presentation

The primary overview presents three feature-local static Research Studies, independent
of Capability request success. The minimal presentation model is `title`, `description`,
`status: completed | incomplete` and optional `route`. It is not an HTTP DTO, Bundle
contract or backend registry. `completed` means an independent Web presentation exists;
it makes no claim about provider/cache readiness, computation success, Bundle admission
or method development. `incomplete` means there is no independent Web entry, not that
the Python research is unimplemented.

In order, 历史基差研究 is completed and navigates to `/research/futures-basis` through
the injected callback; 价格分段研究 and 指数滚动收益研究 are incomplete with no action.
Cards show purpose and completion, not raw identities, commands or readiness fields.
They share the same feature Presentation across runtimes, use responsive Ant Design
layout and provide an explicit keyboard-accessible study action. The secondary
“浏览研究成果” action uses the injected Explorer callback.

Capability discovery and local technical instructions remain in a secondary, initially
collapsed panel. Controller requests, selection, retry, cancellation, stale isolation
and validators remain unchanged. Errors and invalid-contract feedback remain visible
even when the panel is collapsed. Necessary origin/research disclosures appear in a
secondary footer; injected static disclosure retains its exact source meaning.

## Capability and local workflow facts

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

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using validated embedded Examples (retired; Git history), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages.

D2-C implements this boundary. `presentation.ts` exposes the feature-owned `ResearchOverviewPresentation`, pure generated-contract validators (`validateCapabilityList`, `validateCapabilityDetail`, `validateEmbeddedCatalog`) and a feature-local `useStaticCatalog` controller. Production `useCatalog` retains mount list GET, selection-triggered detail GET, independent list/detail retry, cancellation plus request-token stale isolation, protected Auth and HTTP error mapping; `ResearchWorkspacePage` is a thin composition root. Static composition validates the embedded list/detail set, rejects duplicate or unassociated capability identities, selects locally without a GET, and never fabricates a missing detail result. Both runtimes use the same page JSX and feature components. Static origin labels distinguish embedded descriptions from authenticated discovery while preserving published `status` and `live_readiness`. Explorer and Futures Basis navigation remain injected runtime-specific callbacks. [`tests/static/research_catalog/`](../../../tests/static/research_catalog/) is a verification harness using regression data, not an official D3 Example or public Demo entry.

## V2 origin policy reconciliation

Demo Example authority (retired; Git history) owns formal V2 real-market dates and
packaging; authenticity and rights (retired; Git history) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. WP-B implements explicit validated source disclosure through the same Presentation;
private acceptance (retired; Git history) records integration evidence.
Current engineering verification and release boundaries enter through the
implementation handoff (retired; Git history).
