# data_snapshot Capability Catalog

本文件是 `data_snapshot` 的导航 catalog，不定义字段、公式、DTO、失败语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认 Product ownership 与共享能力判断，再从本页选择任务所需的最小 authority 路径。Product 是 primary semantic ownership unit；下列能力的契约由活跃 Product 消费。

本 catalog 用于发现 `data_snapshot` products/capabilities；具体 public Python boundary 由 Product authority 定义，若有 HTTP transport，则从 [ui_http catalog](../ui_http/HTTP_PRODUCTS.md) 进入。

## 产品与场景

| Capability / Product | 定位 | 入口 authority |
| --- | --- | --- |
| CSI1000 IM Basis History | 为 Research 提供显式日期区间内完整的 CSI1000 / IM 年化基差历史 panel | [product authority](src/data_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md) |
| CFFEX Equity Index Futures Basis History | 对单个 IF/IH/IC/IM family 与显式日期区间提供完整历史基差期限结构 | [product authority](src/data_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md) |
| Index Daily History | 为 Research 提供指定指数、显式日期区间及精确观测条数 warm-up 的日线历史 | [product authority](src/data_snapshot/products/index_daily_history/ARCHITECTURE.md) |
| MO Option Chain | 面向读取与可视化消费方的完整 MO 期权链 deterministic data product | [product authority](src/data_snapshot/products/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | 由真实 MO 合约分析 Point 构成的稀疏年化权利金分析产品 | [product authority](src/data_snapshot/products/mo_option_premium/ARCHITECTURE.md) |

## 共享能力

| Capability | 负责内容 | Authority |
| --- | --- | --- |
| Source adapters / Capture facts | 共享 Source endpoint、Capture 身份、公共字段与 minimal normalization；不拥有产品 Source scope | [Capture authority](src/data_snapshot/capture/ARCHITECTURE.md) |
| CFFEX equity-index basis semantics | 两个真实 Product 共用的 family 事实、合约生命周期、四槽、日历距离、基差公式与规范顺序 | [Shared authority](src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md) |

## 路由规则

- 产品任务先进入产品 `ARCHITECTURE.md`，再按其导航选择 co-located data、preparation、read、backend 或 service authority；HTTP specialized authority 从 `ui_http` catalog 进入。`products/<product>/preparation.py` 与 `service.py` 可合法承载产品专属角色。
- 修改共享 Source fact 或 Capture 身份时进入 shared `capture/ARCHITECTURE.md`；产品自己的 universe、窗口、Raw scope 与 completeness 仍由产品 data authority 拥有。
- 修改共用 CFFEX family、slot、remaining days、basis formula 或 ordering 时，进入 [共享 CFFEX basis authority](src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md)，再核对两个 Product 的专属 contract。
- HTTP 实现从 [ui_http catalog](../ui_http/HTTP_PRODUCTS.md) 进入对应 contract，再沿其链接读取 owning product 的最小 semantic authority；不默认读取 sibling product。
- 前端任务先走 `ui_web` authority；只有需要 backend 语义或 transport reconciliation 时才进入这里所列的对应产品文档。
- 外层 `capture/` 承载活跃共享 Source 能力；两个 CFFEX basis Product 共用 `cffex_equity_index_basis` 的确定性语义实现，旧 IM 产品保留兼容导入。能力须由多个真实活跃 Product 的需求支撑；ownership 见 [module architecture](ARCHITECTURE.md)。
