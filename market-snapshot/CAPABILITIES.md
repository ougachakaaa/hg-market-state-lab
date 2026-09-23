# market-snapshot Capability Catalog

本文件是 `market-snapshot` 的导航 catalog，不定义字段、公式、DTO、失败语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认模块边界，再从本页选择任务所需的最小 authority 路径。

## 产品与场景

| Capability / Product | 定位 | 入口 authority |
| --- | --- | --- |
| Daily Market Snapshot | 以最小日行情数据验证 Source → Raw → Preparation 路径的独立场景 | [guides/daily-market-snapshot/index.md](guides/daily-market-snapshot/index.md) |
| CSI1000 5D Analysis | 为外部 analyzer 准备中证1000未来约五个交易日分析所需的确定性数据 | [guides/csi1000-5d-analysis/index.md](guides/csi1000-5d-analysis/index.md) |
| MO Option Chain | 面向读取与可视化消费方的完整 MO 期权链 deterministic data product | [guides/mo-option-chain/index.md](guides/mo-option-chain/index.md) |
| MO Premium Plane | 由真实 MO 合约分析 Point 构成的稀疏年化权利金分析产品 | [guides/mo-option-premium/index.md](guides/mo-option-premium/index.md) |

## 共享能力

| Capability | 负责内容 | Authority |
| --- | --- | --- |
| Source Captures | 共享 Capture 身份、Source endpoint、公共字段与 minimal normalization | [guides/source-captures.md](guides/source-captures.md) |
| Data Services | 用户调用语义、CLI、delivery surface 与 canonical output | [guides/data-services.md](guides/data-services.md) |

## 路由规则

- 先进入产品 `index.md`，再按任务选择 data、preparation、read、backend 或 HTTP contract。
- 修改共享 Source fact 或 Capture 身份时读取 `source-captures.md`；产品自己的 universe、窗口、Raw scope 与 completeness 仍由产品 data authority 拥有。
- HTTP 实现只需产品入口、其 semantic authority 与 HTTP contract；不默认读取 sibling product。
- 前端任务先走 `web-ui` authority；只有需要 backend 语义或 transport reconciliation 时才进入这里所列的对应产品文档。
