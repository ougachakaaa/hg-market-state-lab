# DataLake implementation mapping

本文件只记录 authority 到 implementation 的职责映射，不拥有业务契约，不作为历史施工、状态登记或测试日志。稳定入口为 [ARCHITECTURE.md](ARCHITECTURE.md)；角色语义由 [COMPOSITION.md](COMPOSITION.md)、执行顺序由 [APPLICATION.md](APPLICATION.md)、交接由 [PORTS.md](PORTS.md) 唯一拥有。代码组织变化时同步更新实际职责映射；发现真实 authority / implementation 差异须按 [Agent rules](AGENTS.md) 核对并报告。

## Canonical filesystem

The canonical directory and Python namespace are `data_lake`. The isolated [experiments entry](experiments/README.md) is materialized under [EXPERIMENTS.md](EXPERIMENTS.md), outside formal package wiring.

## 1. 当前实现映射

| Authority responsibility | 当前 implementation seam / 合规含义 |
| --- | --- |
| Kernel Domain / Ports / Application / SQLite Adapter | 分别为 `src/data_lake/domain/`、`ports/`、`application/`、`adapters/outbound/sqlite/`；六边形方向已存在，不重新设计 |
| FetchUnitPlanner | 四个 Dataset `_domain.py::targets`；Calendar 使用 request 展开全部自然日，三个行情 Dataset 使用 request + 固定 days 展开。`Core(..., targets=...)` 是内部 callable 注入参数名称，不是新语义或 mandatory class |
| 可选 Prerequisite Resolver | Calendar 没有 Resolver；三个行情 Dataset `_service.py::trading_days(calendar, request, ensure)` 先验证 public Calendar export，再按授权必要 ensure，重新 export 并验证完整性后返回固定 D；`ensure` bool 是内部 permission 表达，不是 public request 参数 |
| Planning Context / composition | 三个行情 Service `_core` 先验证 request、取得 days、调用 targets，再由 `_composition.py` 把固定 units 注入 Core。Context 以已验证且固定的 days tuple 表达；authority 允许不同载体，不要求新 class/Protocol 或六个参数 |
| UnitRecords 交接 | Calendar Source 返回逐 unit raw row，Domain normalize 转换；三个行情 Source 调用本 Dataset Domain normalize_daily，Domain normalize 接收 UnitRecords。提前转换符合 PORTS.md，不将领域规则所有权移至 Adapter，也不要求重复转换 |
| 写入与读验证 | Core 在 normalize 后调用 check_complete，再调用 Repository.succeed；Core._snapshot 将 CachedUnit facts/basis 还原为 UnitRecords 后重新调用 check_complete。UnitRecords 是载体，现有验证关口必须保留 |
| BatchPlanner | Dataset `_source.py::batches`，Calendar 按自然年分组；Core 在缓存 selection 后调用并验证精确 partition。分组位置不改变 FetchUnit ownership 或逐 unit transaction |

内部 callable 名称、days tuple、bool 或策略 co-location 本身不构成业务缺陷；上述职责映射不要求因角色命名强制创建类、接口或文件。

## 2. Prerequisite validation mapping

三个 consumer 的 `_service.py::_validated_days` 在初次 export 和补齐后的 export 上执行 producer view validation；只有合法 incomplete view 才能触发 owning Dataset 已授权的同范围 ensure。无法取得合法完整前置事实时，在进入 consumer Kernel 前以带 Calendar context 的 OperationError 失败。Read-only operations 不调用 prerequisite ensure。

Calendar producer contract 由 [Calendar SERVICE](datasets/tushare_trade_calendar/SERVICE.md) 拥有，Resolver specialization 分别由 [Index TRADING_DAYS](datasets/tushare_index_daily/TRADING_DAYS.md)、[Futures TRADING_DAYS](datasets/tushare_equity_index_futures/TRADING_DAYS.md) 和 [Options TRADING_DAYS](datasets/tushare_equity_index_options/TRADING_DAYS.md) 拥有；本文件不重复定义契约。历史 V1 验收范围与外部运行证据见非 Authority 的 [Release Acceptance](RELEASE_ACCEPTANCE.md)；当前验证按 Agent rules 执行。
