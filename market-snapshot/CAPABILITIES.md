# market-snapshot Capability Catalog

本文件是 `market-snapshot` 的导航 catalog，不定义字段、公式、DTO、失败语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认模块边界，再从本页选择任务所需的最小 authority 路径。

本 catalog 用于发现 repository products/capabilities，不等同于 `dms list` 或 CLI executable catalog。HTTP-only request-scoped products 仍在此列出，但不因此获得 `dms get` binding。

## 产品与场景

| Capability / Product | 定位 | 入口 authority |
| --- | --- | --- |
| Daily Market Snapshot | 以最小日行情数据验证 Source → Raw → Preparation 路径的独立场景 | [product authority](src/daily_market_snapshot/products/daily_market_snapshot/ARCHITECTURE.md) |
| CSI1000 5D Analysis | 为外部 analyzer 准备中证1000未来约五个交易日分析所需的确定性数据 | [product authority](src/daily_market_snapshot/products/csi1000_5d_analysis/ARCHITECTURE.md) |
| MO Option Chain | 面向读取与可视化消费方的完整 MO 期权链 deterministic data product | [product authority](src/daily_market_snapshot/products/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | 由真实 MO 合约分析 Point 构成的稀疏年化权利金分析产品 | [product authority](src/daily_market_snapshot/products/mo_option_premium/ARCHITECTURE.md) |

## 共享能力

| Capability | 负责内容 | Authority |
| --- | --- | --- |
| Source Captures | 共享 Capture 身份、Source endpoint、公共字段与 minimal normalization | [Capture authority](src/daily_market_snapshot/capture/ARCHITECTURE.md) |
| Data Services | 用户调用语义、CLI、delivery surface 与 canonical output | [Data Service authority](src/daily_market_snapshot/services/ARCHITECTURE.md) |

## 路由规则

- 先进入产品 `ARCHITECTURE.md`，再按其导航选择 co-located data、preparation、read、backend、service 或 HTTP specialized authority。
- 修改共享 Source fact 或 Capture 身份时进入 shared `capture/ARCHITECTURE.md`；产品自己的 universe、窗口、Raw scope 与 completeness 仍由产品 data authority 拥有。
- HTTP 实现只需产品入口、其 semantic authority 与 HTTP contract；不默认读取 sibling product。
- 前端任务先走 `web-ui` authority；只有需要 backend 语义或 transport reconciliation 时才进入这里所列的对应产品文档。
