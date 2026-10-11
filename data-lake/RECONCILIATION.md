# DataLake Implementation reconciliation scope

本文只记录当前实现与已锁定 authority 的结构差距，供下一轮 Implementation Reconciliation 使用；不是第二套 semantic authority，不改变现有 facts、Public API、SQLite generation 或 Source scope。本轮仅编辑 Markdown，以下代码迁移均未实施。目标架构与依赖方向以 [ARCHITECTURE.md](ARCHITECTURE.md) 为准，接入责任以 [COMPOSITION.md](COMPOSITION.md) 为准。

## 当前差距与后续落位

| 当前实现 | 与目标的差距 / 后续 responsibility |
| --- | --- |
| `src/data_lake/_application.py` 在 Application 内定义 Source Protocol，并直接 import `_repository.Repository` / `Snapshot` | Source / Repository capabilities 归 [PORTS.md](PORTS.md)；Application 对端口依赖反转，SQLite 实现归 Kernel outbound adapter。Snapshot 的中立载体与公共计数职责不能由 SQLite 类型迫使 Application 反向依赖具体实现 |
| `src/data_lake/_repository.py` 同时拥有 SQLite 机制与内部 snapshot / coverage aggregates | SQLite lifecycle、hash/count、basis integrity 留在标准 Adapter；snapshot 能力与类型由 Port/Domain 对齐，coverage 语义仍归 Application。可复用计数实现不必机械搬文件，但不能由 Adapter 另定 semantics |
| `src/data_lake/_domain.py`、`_application.py`、`_repository.py` 为 flat layout | 按模块架构的 domain / application / ports / adapters/outbound/sqlite 职责组织；纯 serialization/hash 与 runtime/storage helpers 按实际责任保留，公共 results/errors 不改 contract。不因目标树创建空层或新 framework |
| Calendar `_service.py` 同时包含 targets、normalize、check_complete、project 与 composition；`_source.py` 提供纯 identity/date helpers 和 provider requests | 纯领域策略归 Calendar Domain，transport 归 Calendar Source Adapter，实例绑定与 public delegation 归 Composition Root / Service；保留本 Dataset 六角色绑定与现有 public imports |
| Index/Futures/Options `_source.py` 同时包含 metadata/daily normalization、CompletenessChecker、业务索引与 provider request / paging / partition | 按各 Dataset ARCHITECTURE.md 分离语义责任，Domain 不依赖 Provider/SQLite；Adapter 可调用纯领域策略。避免重复 normalization / validation，不改变当前 catalog proof、metadata reuse、nullable facts 或 expected/observed predicate |
| 三个行情 Dataset `_service.py` 的 `_core` 同时执行 request validation、Calendar public 调用、目标笛卡尔展开及 Kernel binding | Calendar I/O 与 operation 权限留在 Dataset Service orchestration；Target Planner 纯消费固定合法 D；Kernel 只消费最终目标。保留 SSE/CFFEX 选择、先 export/必要时 ensure/再 export、未知目标 OperationError 与独立 storage lifecycle |
| Dataset services 当前通过 `_repository.Repository` 构造自己的存储实例 | 构造具体 Kernel SQLite Adapter 是 Composition Root 的合法职责；后续内部协作按 Repository Port 对齐，不将具体 adapter constructor 泄漏到 consumer 或 Application |

现有实现已具备逐 unit pending/failure/success、原子提交、同一 committed export snapshot、generation 3 frozen basis、Source 惰性初始化与 Provider co-location；这些是要保留的机制，不能以结构迁移重新设计。Dataset 内重复的分页/representation helpers 不自动取得 Kernel ownership；Calendar 调用的相似代码也不授权依赖图引擎。

下一轮可直接按 Kernel 与目标 Dataset authority 实施上述结构 reconciliation，并在实施时调整受影响 architecture tests / internal imports。Provider namespace、现有 execution imports 的兼容要求与 Dataset public surface 仍受模块架构约束。无需新的业务 semantic decision；本轮未发现必须先由用户裁决的 Authority gap。
