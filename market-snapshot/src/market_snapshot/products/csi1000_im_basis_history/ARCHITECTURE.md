# CSI1000 IM Basis History 产品 authority

本文档是 `CSI1000 IM Basis History` 的 bounded-context 入口，拥有产品定位、query identity、跨子契约 invariant 与 authority 路由。模块边界见 [market-snapshot architecture](../../../../ARCHITECTURE.md)。

## 1. Product identity

`CSI1000 IM Basis History` 是一个窄而明确的 historical analysis-ready product，为显式日期区间内的每个实际 CSI1000 交易日产生完整 active IM term-structure basis panel。

```text
CSI1000 index daily facts
+ IM futures basic facts
+ IM futures daily facts
        ↓
deterministic historical Preparation
        ↓
public application result
        ↓
market-research
```

本产品不需要 MO option data，不输出统计 finding、future return、prediction、regime、signal 或 recommendation。

本产品拥有自己的 Application Service 与 public Python request/result/failure/execution contract。Capture 可以在内存中把 query-scoped Source Facts 交给 Preparation；persisted Raw Artifact 不是本产品的成功前提，若使用则只能是本产品自己的 artifact。

## 2. Query identity

Caller 必须显式提供：

```text
start_trade_date    inclusive YYYY-MM-DD
end_trade_date      inclusive YYYY-MM-DD
```

Normalized query identity 为 `start_trade_date + end_trade_date`。`start_trade_date <= end_trade_date` 是成功请求的必要条件。不使用 request time、`today`、`latest`、implicit historical window 或自动 fallback。

## 3. Ownership

| Owner | Canonical knowledge |
| --- | --- |
| 本文档 | 产品身份、query identity、跨子契约 invariant |
| [Shared Source Capture authority](../../capture/ARCHITECTURE.md) | Capture identity、Source endpoint、公共 Source facts 与 minimal normalization |
| [Shared CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) | family/underlying/listing facts、active contract lifecycle、slot、remaining days、basis formulas、validation 与 canonical observation ordering |
| [Product basis compatibility authority](im-basis-semantics.md) | 本产品的 IM-only 使用与旧 public contract 兼容说明 |
| [Data authority](data.md) | 本产品 Source scope、observation dates 与 Source completeness |
| [Read/application contract](read-contract.md) | Preparation projection、semantic result、public application boundary 与 failure |

## 4. Stable invariants

1. 结果是完整的 `trade_date × active IM contract` panel，不按 liquidity 或 Research preference 筛选。
2. IM slot、calendar distance、basis formula 与 ordering 服从共享 CFFEX basis authority；本产品保持其既有 public request/result/execution contract。
3. 必需的 underlying、contract 或 daily fact 缺失、重复、冲突或不可唯一映射时，整个 request 失败，不返回 partial panel。
4. Public result 是 semantic Python application result，Research 无需了解 Raw、Preparation implementation 或 persistence layout。
5. 相同 Source facts、query 与 Preparation Definition 必须得到语义一致的 result。

## 5. V1 non-goals

```text
MO option data
volume/OI-based filtering or interpretation
main-contract selection
persisted final artifact
HTTP endpoint
database or cache
generic historical query API
Research statistics or plots
future-return / predictive analysis
```

## 6. Navigation

- 修改 Source scope、observation dates 或 Source completeness → [data authority](data.md)
- 修改 result shape、Preparation projection、public boundary 或 product failure → [read/application contract](read-contract.md)
- 修改共用 slot、remaining days、basis formula、validation 或 canonical ordering → [Shared CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md)，并核对 [本产品兼容说明](im-basis-semantics.md)
- 修改 retained study method → [IM Annualized Basis Baseline study](../../../../../market-research/studies/im_basis_baseline/ARCHITECTURE.md)

只读取当前任务需要的分支；本产品不依赖 sibling product authority 或产物。
