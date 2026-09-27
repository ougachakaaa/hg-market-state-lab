# IM Basis Research Semantics authority

本文档是两个现有 IM basis retained studies 共用的 predictor semantic owner。Research 边界见 [market-research architecture](../../ARCHITECTURE.md)；empirical quantile 见 [shared distribution authority](../distribution/ARCHITECTURE.md)；输入产品见 [CSI1000 IM Basis History](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md)。

本 authority 只拥有 `non_front_mean_basis` 的 IM-basis-specific predictor semantics。它不是 empirical quantile 的 owner，也不是通用 feature framework、statistics framework、Snapshot Preparation semantic 或 Modeling semantic。

## Daily predictor

对 `CSI1000 IM Basis History` public result 中每个完整 observation date `T`：

```text
non_front_mean_basis_T
= arithmetic mean(
    M1 annualized_basis_pct,
    Q1 annualized_basis_pct,
    Q2 annualized_basis_pct
  )
```

该 predictor 是不加权算术平均，严格排除 `M0`。不使用 volume、open interest、liquidity、main-contract designation 或 days-to-delist weighting，也不使用其他 slot selection。

`annualized_basis_pct` 沿用 Snapshot 的 percentage points annualized 单位。本 authority 不重新定义 `M0/M1/Q1/Q2`、remaining days、basis 或 annualization formula；这些语义由 Snapshot 的 [CSI1000 IM Basis History 产品内 basis authority](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/im-basis-semantics.md) 拥有。Research 只消费该产品的公开 application result。

输入产品已保证每个 observation date 四槽完整且唯一。Consumer 看到缺槽、重复 slot、不可计算值或 partial date 时，必须将其视为 upstream contract violation 并失败，不填补、删除或重新选择合约。

## Consumers and ownership boundary

当前 consumers：

- [IM Annualized Basis Baseline](../../studies/im_basis_baseline/ARCHITECTURE.md)
- [IM Basis Forward Return Association](../../studies/im_basis_forward_return_association/ARCHITECTURE.md)

这两个 Study 都直接消费 Snapshot public semantic result；后者不依赖前者的 persisted result。`non_front_mean_basis` 只是当前 Research 中的共用 predictor，不因多个 Research consumer 而成为 Snapshot field、production feature、forecast、signal 或 Modeling contract。

只有该 predictor 的 IM basis semantics 改变时才修改本文档。Quantile convention 由 [shared distribution authority](../distribution/ARCHITECTURE.md) 拥有；各 Study 的 question、target、sample、method、result 与 limitation 不上提至此。
