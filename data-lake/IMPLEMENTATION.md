# DataLake authority / implementation reconciliation

本文件只记录当前 authority 到 implementation 的映射与尚未处理的差异，不拥有业务契约，不作为历史施工或测试日志。稳定入口为 [ARCHITECTURE.md](ARCHITECTURE.md)；角色语义由 [COMPOSITION.md](COMPOSITION.md)、执行顺序由 [APPLICATION.md](APPLICATION.md)、交接由 [PORTS.md](PORTS.md) 唯一拥有。当前核对基准为 `04e85172d2b9a1452aa36c5bc7e318830795634e`；本次 reconciliation 仅修改 authority，不修改 Python、SQLite schema、public API 或 tests。后续代码变更须同步更新这里的当前状态。

## 1. 当前实现映射

| Authority responsibility | 当前 implementation seam / 合规含义 |
| --- | --- |
| Kernel Domain / Ports / Application / SQLite Adapter | 分别为 `src/data_lake/domain/`、`ports/`、`application/`、`adapters/outbound/sqlite/`；六边形方向已存在，不重新设计 |
| FetchUnitPlanner | 四个 Dataset `_domain.py::targets`；Calendar 使用 request 展开全部自然日，三个行情 Dataset 使用 request + 固定 days 展开。`Core(..., targets=...)` 是内部 callable 注入参数名称，不是新语义或 mandatory class |
| 可选 Prerequisite Resolver | Calendar 没有 Resolver；三个行情 Dataset `_service.py::trading_days(calendar, request, ensure)` 已执行授权 public Calendar export / 必要 ensure，并返回固定 D；`ensure` bool 是现有内部 permission 表达，不是 public request 参数 |
| Planning Context / composition | 三个行情 Service `_core` 先验证 request、取得 days、调用 targets，再由 `_composition.py` 把固定 units 注入 Core。当前 context 以 days tuple 表达，未独立保留完整 view；authority 允许不同载体，不要求新 class/Protocol 或六个参数 |
| UnitRecords 交接 | Calendar Source 返回逐 unit raw row，Domain normalize 转换；三个行情 Source 调用本 Dataset Domain normalize_daily，Domain normalize 接收 UnitRecords。提前转换符合 PORTS.md，不将领域规则所有权移至 Adapter，也不要求重复转换 |
| 写入与读验证 | Core 在 normalize 后调用 check_complete，再调用 Repository.succeed；Core._snapshot 将 CachedUnit facts/basis 还原为 UnitRecords 后重新调用 check_complete。UnitRecords 是载体，现有验证关口必须保留 |
| BatchPlanner | Dataset `_source.py::batches`，Calendar 按自然年分组；Core 在缓存 selection 后调用并验证精确 partition。分组位置不改变 FetchUnit ownership 或逐 unit transaction |

代码使用旧内部 callable 名称、days tuple、bool 或策略 co-location 本身不构成业务缺陷；后续 Coding Agent 应按上述职责映射实现新的 authority 表达，不因角色命名强制创建类、接口或文件。

## 2. 已确认未处理的差异与后续任务

### Calendar consumer Resolver 的合法 view 校验

Owning contract 是三个 consumer 的 [Index TRADING_DAYS](datasets/tushare_index_daily/TRADING_DAYS.md)、[Futures TRADING_DAYS](datasets/tushare_equity_index_futures/TRADING_DAYS.md)、[Options TRADING_DAYS](datasets/tushare_equity_index_options/TRADING_DAYS.md)，producer contract 是 [Calendar SERVICE](datasets/tushare_trade_calendar/SERVICE.md)。

当前三个 `_service.py::trading_days` 检查 dataset/view、exchange、window、自然日序列、coverage 数量与部分 Record types，但没有校验 export_schema_version，也没有完整校验 envelope / coverage semantic types（例如 Python bool 可以通过整数相等比较）。这些 checks 尚不足以证明 producer view 完全符合已发布 contract，不能将本轮 authority 收敛报告为 implementation 已完成。

后续任务：按上述 narrowest contract 补齐 producer view validation，拒绝错误版本、类型、范围、计数与非法 facts，保留 Calendar context 的 OperationError；同时保持三个 consumer 已声明 SSE/CFFEX selection、只读链、完整目标、计数及空 D 语义。可复用验证逻辑，但依赖绑定与 operation permission 仍由 owning Dataset Composition 提供，不创建全局 Resolver registry 或 Kernel Calendar knowledge。

### Prerequisite ensure 前的合法性关口

当前 `trading_days` 在完整合法性检查前，先根据 `not view.coverage.complete and ensure` 决定是否调用 Calendar ensure。因此非法但标记 incomplete 的 view 可以先触发 producer mutation，之后才被拒绝。Owning contract 仍是上述三个 TRADING_DAYS.md 与 APPLICATION.md；prerequisite ensure 只用于补齐合法且与请求匹配的 incomplete view，不用于修复 view 身份/格式错误。

后续任务：先确认初次 export 的 envelope、request 对应关系、互斥计数和已有 rows 合法，再决定是否获准 ensure；补齐后重新 export 并验证完整 view，再发布 Validated Planning Context。Prerequisite 不可用时不要查询或写 consumer units，不把错误编码为 consumer UnitFailure；producer 此前已提交的事实不跨库 rollback。

上述任务只记录，不在本轮修复或修改测试。完成时须验证 Calendar producer 与三个 consumer，尤其 read-only 权限、非法 view 拒绝、同范围 ensure 与目标固定；验证命令遵循 [AGENTS.md](AGENTS.md)，不使用真实凭据或缓存。
