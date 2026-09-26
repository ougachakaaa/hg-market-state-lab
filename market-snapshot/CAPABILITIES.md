# market-snapshot Capability Catalog

本文件是 `market-snapshot` 的导航 catalog，不定义字段、公式、DTO、失败语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认模块边界，再从本页选择任务所需的最小 authority 路径。

本 catalog 用于发现 `market-snapshot` products/capabilities，不等同于 `dms list`、CLI executable catalog 或 repository HTTP catalog。Request-scoped products 仍在此列出，但不因此获得 `dms get` binding；其 HTTP transport 从 [backend-api catalog](../backend-api/HTTP_PRODUCTS.md) 进入。

## 产品与场景

| Capability / Product | 定位 | 入口 authority |
| --- | --- | --- |
| Daily Market Snapshot | 以最小日行情数据验证 Source → Raw → Preparation 路径的独立场景 | [product authority](src/market_snapshot/products/daily_market_snapshot/ARCHITECTURE.md) |
| CSI1000 5D Analysis | 为外部 analyzer 准备中证1000未来约五个交易日分析所需的确定性数据 | [product authority](src/market_snapshot/products/csi1000_5d_analysis/ARCHITECTURE.md) |
| CSI1000 IM Basis History | 为 Research 提供显式日期区间内完整的 CSI1000 / IM 年化基差历史 panel | [product authority](src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md) |
| MO Option Chain | 面向读取与可视化消费方的完整 MO 期权链 deterministic data product | [product authority](src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | 由真实 MO 合约分析 Point 构成的稀疏年化权利金分析产品 | [product authority](src/market_snapshot/products/mo_option_premium/ARCHITECTURE.md) |

## 共享能力

| Capability | 负责内容 | Authority |
| --- | --- | --- |
| Source Captures | 共享 Capture 身份、Source endpoint、公共字段与 minimal normalization | [Capture authority](src/market_snapshot/capture/ARCHITECTURE.md) |
| IM Basis Preparation Semantics | 共享 IM 期限位置、剩余日历天数与基差公式 | [IM basis authority](src/market_snapshot/preparation/im_basis/ARCHITECTURE.md) |
| Data Services | application request/result、orchestration、semantic failure、CLI 与 canonical persisted output | [Data Service authority](src/market_snapshot/services/ARCHITECTURE.md) |

## 路由规则

- 先进入产品 `ARCHITECTURE.md`，再按其导航选择 co-located data、preparation、read、backend 或 service authority；HTTP specialized authority 从 `backend-api` catalog 进入。
- 修改共享 Source fact 或 Capture 身份时进入 shared `capture/ARCHITECTURE.md`；产品自己的 universe、窗口、Raw scope 与 completeness 仍由产品 data authority 拥有。
- 修改被多个产品复用的 IM slot、remaining days 或 basis formula 时进入 shared IM basis authority；产品 query、result 与 completeness 不上提到 shared capability。
- HTTP 实现从 [backend-api catalog](../backend-api/HTTP_PRODUCTS.md) 进入对应 contract，再沿其链接读取 owning product 的最小 semantic authority；不默认读取 sibling product。
- 前端任务先走 `web-ui` authority；只有需要 backend 语义或 transport reconciliation 时才进入这里所列的对应产品文档。
