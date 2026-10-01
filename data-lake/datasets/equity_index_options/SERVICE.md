# equity_index_options Public Application Service authority

本文件拥有 Options 的稳定 public service boundary 与未决 consumer details，继承 [Dataset architecture](ARCHITECTURE.md) 与公共 [APPLICATION.md](../../APPLICATION.md)。本轮是 partial semantic authority，尚未发布完整 request/view schema。

## 1. 已锁定 operation family

本 Dataset 独立拥有 transport-neutral Python semantic service，目标 public namespace 为 `data_lake.datasets.equity_index_options`，本轮没有可 import package。下表 semantic_request 是待决 Scope/Window 的概念占位，不是已发布 Python type：

| Operation | Stable contract |
| --- | --- |
| coverage(semantic_request) → CoverageResult | 查询目标 units 当前完整成功缓存；禁止 Source I/O、mutation、隐式 ensure |
| ensure(semantic_request) → EnsureResult | 执行 missing/non-success units、默认跳过 success，依最终确认的 completeness 逐 unit 原子保存 |
| export(semantic_request) → Options Market Facts View | Dataset-owned business view 与公共 Export Envelope；read-only、不写文件 |

不新增 sync/read/daily-update verbs，不要求通用 facade/registry。Caller 不提供 SQLite path、Repository、Source adapter、token 或 internal unit/record IDs。Concrete service/factory/request types 在 domain decisions 确认后编码，不通过一个提前定型的 contract/date signature 决定粒度。

公共 result fields、互斥计数、complete、success/freshness、UnitFailure 与两类 application errors 继承 APPLICATION.md。Failure identity 必须使用最终 semantic FetchUnit identity；本轮不定义 shape、requested_units/records_written 公式或 chain-success 判定。

## 2. 已锁定 export boundary

Export envelope 必须有 dataset（固定 `equity_index_options`）、view、export_schema_version、scope、window、coverage 与 Dataset-owned business payload。View 应能表达 contract identity、product、expiry、strike、CALL/PUT、exchange、underlying semantic identity、lifecycle 与 Source market facts。

只返回目标范围内 success units 的合法 facts，incomplete coverage 可返回已缓存的部分 view，准确声明 coverage；无 facts 时具有明确 empty payload。Coverage 与 payload 来自同一个 Options committed snapshot，不通过其他 Dataset persistence 或 snapshot产品内部结果组装。

禁止 SQLite path、unit/record IDs、Repository、provider response object、transport metadata 与 derived IV/moneyness/DTE/risk-premium/research features。Underlying identity 是 relationship fact，不保证 Index 已有行情，不构成 runtime dependency 或 foreign key。

## 3. 尚待人工决定的 consumer details

Domain 待决项由 ARCHITECTURE.md 第 3 节唯一拥有；确认以后才固定：

- Concrete request fields/types、selection normalization / validation、Window interpretation 与目标展开。
- UnitFailure semantic identity、accounting specialization、incomplete chain/cross-section 的结果语义。
- View identity、首次 export_schema_version、payload 名称/shape、required facts、types、units、ordering 与 empty representation。
- Provider runtime composition / credential convention（复用 repository 既有约定）、factory 与 facade 概念。

未定 chain/universe 不能默认为空并返回 complete=true；没有新 Calendar/Index/Futures dependency permission。InvalidRequestError、OperationError 与可恢复 unit failure 使用公共 taxonomy，不新增 transport exceptions，也不提前实现尚未决定的 validation。
