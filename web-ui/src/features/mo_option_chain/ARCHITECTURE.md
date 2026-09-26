# MO Option Chain visualization bounded-context authority

本文件是该 frontend vertical slice 的入口，并在 [web-ui architecture](../../../ARCHITECTURE.md) 边界内 specialize [presentation architecture](../../../presentation-architecture.md)。

## Ownership

本 context 拥有日期输入、presentation state、visual encoding、interaction、formatting 与用户可见 empty/error presentation。它只消费 `market-snapshot` read result 与 `backend-api` HTTP contract，不拥有 Source、contract universe、price fallback、formula 或 completeness。

## Navigation

- 用户体验、combined chart、viewport、颜色、精度与状态：[visualization.md](visualization.md)
- Backend product identity/read semantics：[MO Option Chain authority](../../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md)
- HTTP wire contract：[backend-api HTTP authority](../../../../backend-api/products/mo_option_chain/http-contract.md)
