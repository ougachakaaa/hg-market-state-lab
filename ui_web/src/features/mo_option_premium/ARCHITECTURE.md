# MO Premium Plane frontend bounded-context authority

本文件是 MO Premium Plane frontend vertical slice 的入口，并在 [ui_web architecture](../../../ARCHITECTURE.md) 边界内 specialize [presentation architecture](../../../presentation-architecture.md)。它与 `mo_option_chain` 是 sibling frontend slices，不共享产品 identity 或 visualization semantics。

## 1. Identity and Dependency

```text
MO Premium Plane frontend
        consumes
GET /mo-option-premium-plane
```

本 slice 展示 backend 已完成的 MO multidimensional-premium sparse plane。它不从 Option Chain response 派生 Premium Plane，也不扩展 Option Chain frontend。

依赖方向固定为：

```text
data_snapshot Premium semantic contract
        ↓
ui_http Premium HTTP contract / generated client types
        ↓
frontend request adaptation
        ↓
presentation and interaction
```

## 2. Frontend Ownership

本 context 只拥有：

```text
explicit query input
presentation state
formatting and table projection
interaction
user-visible empty, loading and error presentation
```

它不得：

- 从 Option Chain DTO 或其他 frontend state 重新计算 Premium Plane；
- 重新计算 DTE 或任一四维 Premium metric coordinate，尤其不得从 points、premium、strike、underlying 或 futures 推导 reference-relative、annualized 或 yield metric；
- fallback underlying 或 futures，插值或替代 strike，或生成 synthetic analytical Point、contract、cell/null fact；
- 合并 Point absence、Point 中的 null fact 与 numeric zero；
- 推断 cheap/expensive、推荐 strike、市场判断、交易信号或 decision semantics。

## 3. Stable Invariants

1. 一个成功 response 是当前 query 的完整 backend sparse plane；frontend 展示只做可逆的 presentation projection；CSV 是遵循 [Copy / Export authority](../../../data-copy-export.md) 的衍生表示，不要求可逆。
2. HTTP query identity 与 local presentation state 分离；Call/Put、`Reference Basis`、`Value Basis`、`Time Normalization`、`Representation` 与 expiry visibility 不触发 backend recomputation 或新请求。
3. Table coordinate 必须对应真实 Point 才拥有 analytical observation；frontend grid 本身不创造事实。
4. Backend ordering、identity、null/zero/absence 与 reference availability 必须保留；formatting 不改变 numeric facts。
5. 新 query 的旧 response 不得作为当前 observation 展示，较早请求不得覆盖较新 query 的结果。
6. Table rows 是 selected side 与 selected expiries 下全部真实 Point strikes 的 numeric union；frontend 不按 reference price 或显示范围删除真实 Point。
7. Strike relative-to-reference coloring 只属于 presentation，不创建 analytical metric、Point 或市场判断，也不由 selected metric reference basis 控制。
8. Production 的 Raw HTTP Response Inspector 只展示当前成功 Premium request 实际收到且通过 runtime validation 的完整 JSON payload；它不是 Source Raw、Premium Raw Artifact、canonical Point 或 table projection，也不受 local presentation state 影响。
9. query identity 改变后，旧 raw payload 与旧 validated response 同时退出 current-result 状态；idle、loading 与 failure 均不得把上一笔成功 payload 标记为当前原始响应。

## 4. Navigation

- V1 用户流程、query/presentation state、numeric plane、formatting、interaction 与用户可见状态：[visualization.md](visualization.md)
- Backend product identity 与跨层 invariant：[MO Premium Plane product authority](../../../../data_snapshot/src/data_snapshot/products/mo_option_premium/ARCHITECTURE.md)
- HTTP resource、wire projection、ordering 与 error mapping：[ui_http HTTP contract](../../../../ui_http/products/mo_option_premium/http-contract.md)

只沿当前任务需要的分支继续读取。Frontend implementation 不需要读取 backend Source、Raw、formula、Preparation 或 orchestration authority。

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using validated embedded Examples (retired; Git history), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. In Demo, the Inspector displays the complete validated embedded Example payload with an explicit static origin label distinguishing V2 real-market data from Synthetic test data; it must not claim an HTTP response was received. Shared presentation remains here, not in parallel Demo pages. D2-B implements this boundary through `presentation.ts`: shared page composition,
`usePremiumPresentation(validatedPlane)` and pure generated-contract validation. Production
retains query, cancellation, stale-response and Auth lifecycle in `usePremiumPlane`.
Every new query resets presentation; every replacement static result starts with the
formal defaults and all expiries selected. Raw JSON/Context/Inspector retain the exact
validated payload object, while CSV uses its validated plane. The pure validator preserves
the nonempty-Points success invariant. [`tests/static/mo_option_premium/`](../../../tests/static/mo_option_premium/) is a verification harness using
regression data, not an official Example or public Demo entry.

## V2 origin policy reconciliation

Demo Example authority (retired; Git history) owns formal V2 real-market dates and
packaging; authenticity and rights (retired; Git history) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. WP-B implements explicit validated source disclosure through the same Presentation;
private acceptance (retired; Git history) records integration evidence.
Current engineering verification and release boundaries enter through the
implementation handoff (retired; Git history).
