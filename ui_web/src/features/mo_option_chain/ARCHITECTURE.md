# MO Option Chain visualization bounded-context authority

本文件是该 frontend vertical slice 的入口，并在 [ui_web architecture](../../../ARCHITECTURE.md) 边界内 specialize [presentation architecture](../../../presentation-architecture.md)。

## Ownership

本 context 拥有日期输入、presentation state、visual encoding、interaction、formatting 与用户可见 empty/error presentation。它只消费 `data_snapshot` read result 与 `ui_http` HTTP contract，不拥有 Source、contract universe、price fallback、formula 或 completeness。

## Navigation

- 用户体验、combined chart、viewport、颜色、精度与状态：[visualization.md](visualization.md)
- Backend product identity/read semantics：[MO Option Chain authority](../../../../data_snapshot/src/data_snapshot/products/mo_option_chain/ARCHITECTURE.md)
- HTTP wire contract：[ui_http HTTP authority](../../../../ui_http/products/mo_option_chain/http-contract.md)

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using [validated committed Examples](../../demo/EXAMPLES.md), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages. D2-A implements this boundary: `page/OptionChainPage.tsx` composes the production
query controller with `page/OptionChainPresentation.tsx`. Static consumers enter through
`presentation.ts`, supplying a validated complete result, fixed query identity and source
disclosure, plus `useOptionChainPresentation(result)` local state. The hook resets expiry
selection on result replacement while retaining colors and viewport. `api/validateOptionChain.ts`
owns pure generated-contract validation; it imports no request/auth implementation.
The static verification harness under `testing/static/` is test data/composition only,
not a published Example or Demo V2 entry.
