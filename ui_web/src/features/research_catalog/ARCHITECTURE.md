# Research Catalog & Workspace authority

This read-only frontend slice owns the topic-oriented Research Overview and discovery at `/research`. Research
owns case and capability semantics; [Research capability publication](../../../../market_research/descriptive/RESEARCH_CAPABILITY.md)
and the [HTTP contract](../../../../ui_http/products/research/http-contract.md) own the
online descriptor. This slice consumes only the two Capability GET operations through
its generated OpenAPI contract. It does not preview, execute, probe market availability,
or create Research results.

## Research Study presentation

The primary overview presents feature-local Research Studies, independent
of Capability request success. The minimal presentation model is `title`, `description`,
`status: completed | incomplete` and optional `route`. It is not an HTTP DTO, Bundle
contract or backend registry. `completed` means an independent Web presentation exists;
it makes no claim about provider/cache readiness, computation success, Bundle admission
or method development. `incomplete` means there is no independent Web entry, not that
the Python research is unimplemented.

In order, 历史基差研究 is completed and navigates to `/research/futures-basis` through
the injected callback; Production also exposes completed 历史跨期相对价值研究 at
`/research/calendar-spread-relative-value` through its own injected callback. Static
omits that card until WP7 Bundle admission. 价格分段研究 and 指数滚动收益研究 are incomplete with no action.
Cards show purpose and completion (已完成 in success-colored text, 未完成 in secondary gray text), not raw identities, commands or readiness fields.
They share the same feature Presentation across runtimes, use responsive Ant Design
layout and provide an explicit keyboard-accessible study action. The overview contains
only its heading, Study cards, completion statuses, available study navigation and
minimal footer disclosure. It exposes no Explorer action, Capability list, technical
selection, raw descriptors or local workflow instructions. Catalog-only failures are
not presented because their results are not displayed. Authentication remains owned
by the application boundary. Controller requests, selection, retries, cancellation,
stale isolation and formal validation remain independently testable and unchanged.
Explorer remains registered at `/research/publications` for direct URL and history.
Injected static disclosure retains its exact source meaning.

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using validated embedded Examples (retired; Git history), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages.

D2-C implements this boundary. `presentation.ts` exposes the feature-owned `ResearchOverviewPresentation`, pure generated-contract validators (`validateCapabilityList`, `validateCapabilityDetail`, `validateEmbeddedCatalog`) and a feature-local `useStaticCatalog` controller. Production `useCatalog` retains mount list GET, selection-triggered detail GET, independent list/detail retry, cancellation plus request-token stale isolation, protected Auth and HTTP error mapping; `ResearchWorkspacePage` is a thin composition root. Static composition validates the embedded list/detail set, rejects duplicate or unassociated capability identities, selects locally without a GET, and never fabricates a missing detail result. Both runtimes use the same page JSX and feature components. Catalog facts remain validated independently of the Study-only presentation. Explorer and Futures Basis navigation remain injected runtime-specific callbacks. [`tests/static/research_catalog/`](../../../tests/static/research_catalog/) is a verification harness using regression data, not an official D3 Example or public Demo entry.

## V2 origin policy reconciliation

Demo Example authority (retired; Git history) owns formal V2 real-market dates and
packaging; authenticity and rights (retired; Git history) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. WP-B implements explicit validated source disclosure through the same Presentation;
private acceptance (retired; Git history) records integration evidence.
Current engineering verification and release boundaries enter through the
implementation handoff (retired; Git history).
