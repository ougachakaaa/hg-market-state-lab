# CSI1000 5D Analysis 产品 authority

本文档是 CSI1000 未来约五个交易日分析数据产品的 bounded-context 入口，只拥有产品定位、职责边界、稳定 invariant 与下层导航。模块架构见 [market-snapshot architecture](../../../../ARCHITECTURE.md)。

## 1. 产品定位

本产品以显式目标交易日为观察基准，为外部 Analyzer 准备足够的数据，使其能够分析未来约五个交易日的中证1000市场状态。

`market-snapshot` 只负责确定性数据准备，不定义或输出价格中枢、正常波动区域、反向交易候选、bullish/bearish、概率、目标点位或交易建议。

## 2. 产品边界

```text
shared Source Capture capabilities
        ↓
CSI1000 5D goal-scoped Raw Artifacts
        ↓
CSI1000 5D Analysis Preparation
        ↓
analysis-ready snapshot.json
        ↓
external Analyzer
```

该产品可以复用共享 Capture capability，但拥有自己的 Raw scope、历史窗口和最终 artifact；它不定义 MO Option Chain 或 MO Premium Plane 的产品语义。上述 goal-scoped Raw Artifacts 是本产品选择的 persisted Capture/Preparation 契约。Application Service、执行顺序、结果发布与失败语义归本产品所有；外层 `services/` 只提供共享 CLI binding 与 persisted delivery 约定。

## 3. Stable Invariants

1. 目标交易日由调用方显式给出，不使用 `today`、`latest` 或自动 fallback。
2. Source Capture 保留 Source fact；窗口、join、分析命名和派生公式只在 Analysis Preparation 中发生。
3. Preparation 只读取本产品 goal-scoped Raw Artifacts，不访问 Source 或其他产品产物。
4. 相同 Raw Artifacts 与 Preparation Definition 必须得到语义一致的输出。
5. 必需事实或派生输入缺失时显式失败；Source 合法 null 按 preparation authority 保留，不补零或估算。
6. 输出是 analysis-ready data，不包含市场判断或交易结论。
7. IM active universe、contract slot、remaining days 与 basis formula 统一引用 [shared IM basis authority](../../preparation/im_basis/ARCHITECTURE.md)，本产品不维护平行定义。

## 4. Service Orchestration

一次 `target_trade_date = D` 请求严格按以下阶段执行，失败立即停止，不运行后续阶段：

```text
CSI1000 history Capture
→ MO option basic Capture
→ MO option daily Capture
→ IM futures basic Capture
→ IM futures daily Capture
→ Analysis Preparation
→ publish output/csi1000-5d-analysis/D/snapshot.json
```

Service 可以复用同一请求已取得的 basic contract facts；它不拥有 Source endpoint 参数或 Preparation formula。

## 5. Navigation

- Source Capture 共享身份与公共字段语义：[Capture authority](../../capture/ARCHITECTURE.md)
- 共享 IM slot、remaining days 与 basis 语义：[IM basis authority](../../preparation/im_basis/ARCHITECTURE.md)
- 本产品所需 Source、Raw、universe、历史窗口与 completeness：[data.md](data.md)
- Raw → `snapshot.json` 的结构、join、公式、null 与失败语义：[preparation-contract.md](preparation-contract.md)
- 本产品 Application Service 的 orchestration 与 result publication：本文档和 [Preparation authority](preparation-contract.md)；共享 CLI binding 与 persisted output convention：[delivery authority](../../services/ARCHITECTURE.md)

只实现 Capture 或 Raw scope 时无需读取 Preparation 的全部公式；只实现 Preparation 时需要本文档、`data.md` 与 `preparation-contract.md`，无需读取其他产品 authority。
