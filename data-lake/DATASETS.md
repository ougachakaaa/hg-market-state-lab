# DataLake DataSets catalog

本文件只提供自治 Dataset bounded context 的 authority navigation，不是 runtime registry，不拥有 Dataset loading 或 service routing。模块 ownership 见 [ARCHITECTURE.md](ARCHITECTURE.md)，公共领域与 persistence invariants 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md)，公共 Application contract 见 [APPLICATION.md](APPLICATION.md)；Dataset-specific semantics 由对应 authority 拥有，不在 catalog 复制 schema。

| Canonical Dataset identity | Bounded-context / domain entry | Consumer contract |
| --- | --- | --- |
| `tushare_trade_calendar` | [Dataset architecture](datasets/tushare_trade_calendar/ARCHITECTURE.md) | 经 domain entry 进入 [SERVICE.md](datasets/tushare_trade_calendar/SERVICE.md) |
| `tushare_index_daily` | [指数日线 architecture](datasets/tushare_index_daily/ARCHITECTURE.md) | 经 domain entry 进入 [SERVICE.md](datasets/tushare_index_daily/SERVICE.md) |
| `tushare_equity_index_futures` | [股指期货 architecture](datasets/tushare_equity_index_futures/ARCHITECTURE.md) | 经 domain entry 进入 [SERVICE.md](datasets/tushare_equity_index_futures/SERVICE.md) |
| `tushare_equity_index_options` | [股指期权 architecture](datasets/tushare_equity_index_options/ARCHITECTURE.md) | 经 domain entry 进入 [SERVICE.md](datasets/tushare_equity_index_options/SERVICE.md) |

Domain 任务从 Dataset architecture 选择所需 FACTS、CONTRACT_UNIVERSE、TRADING_DAYS 等专题；Composition 任务先读公共 [COMPOSITION.md](COMPOSITION.md)，再进入目标 Dataset architecture 的六角色绑定与职责组织；consumer 任务继续进入 SERVICE.md；CLI adapter 再进入 lab authority。Catalog 不拥有 contract，也不声明 capability 已实现。
