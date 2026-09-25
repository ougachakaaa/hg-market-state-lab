# MO Premium Plane frontend bounded-context authority

本文件是 MO Premium Plane frontend vertical slice 的入口，并 specialize [web-ui architecture](../../../ARCHITECTURE.md)。它与 `mo_option_chain` 是 sibling frontend slices，不共享产品 identity 或 visualization semantics。

## 1. Identity and Dependency

```text
MO Premium Plane frontend
        consumes
GET /mo-option-premium-plane
```

本 slice 展示 backend 已完成的 MO annualized-premium sparse plane。它不从 Option Chain response 派生 Premium Plane，也不扩展 Option Chain frontend。

依赖方向固定为：

```text
Premium backend semantic contract
        ↓
Premium HTTP contract / generated client types
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
- 重新计算 DTE、annualized premium points、annualized time-value points 或 seller premium yield，尤其不得从 premium、strike、underlying 或 futures 推导 time-value metric；
- fallback underlying 或 futures，插值或替代 strike，或生成 synthetic analytical Point、contract、cell/null fact；
- 合并 Point absence、Point 中的 null fact 与 numeric zero；
- 推断 cheap/expensive、推荐 strike、市场判断、交易信号或 decision semantics。

## 3. Stable Invariants

1. 一个成功 response 是当前 query 的完整 backend sparse plane；frontend 只做可逆的 presentation projection。
2. HTTP query identity 与 local presentation state 分离；Call/Put、metric 与 expiry visibility 不触发 backend recomputation 或新请求。
3. Table coordinate 必须对应真实 Point 才拥有 analytical observation；frontend grid 本身不创造事实。
4. Backend ordering、identity、null/zero/absence 与 reference availability 必须保留；formatting 不改变 numeric facts。
5. 新 query 的旧 response 不得作为当前 observation 展示，较早请求不得覆盖较新 query 的结果。
6. Table rows 是 selected side 与 selected expiries 下全部真实 Point strikes 的 numeric union；frontend 不按 reference price 或显示范围删除真实 Point。
7. Strike relative-to-reference coloring 只属于 presentation，不创建 analytical metric、Point 或市场判断。

## 4. Navigation

- V1 用户流程、query/presentation state、numeric plane、formatting、interaction 与用户可见状态：[visualization.md](visualization.md)
- Backend product identity 与跨层 invariant：[MO Premium Plane product authority](../../../../market-snapshot/src/daily_market_snapshot/products/mo_option_premium/ARCHITECTURE.md)
- HTTP resource、wire projection、ordering 与 error mapping：[HTTP contract](../../../../market-snapshot/src/daily_market_snapshot/products/mo_option_premium/http-contract.md)

只沿当前任务需要的分支继续读取。Frontend implementation 不需要读取 backend Source、Raw、formula、Preparation 或 orchestration authority。
