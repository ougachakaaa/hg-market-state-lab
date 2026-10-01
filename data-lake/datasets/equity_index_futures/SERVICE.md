# equity_index_futures Public Application Service authority

本文件拥有 Futures 的稳定 public service boundary 与未决 consumer contract，继承 [Dataset architecture](ARCHITECTURE.md) 及公共 [APPLICATION.md](../../APPLICATION.md)。本轮是 partial semantic authority，尚不构成可实现的完整 request/view schema。

## 1. 已锁定 operation family

本 Dataset 独立发布 transport-neutral Python semantic service，目标 public namespace 为 `data_lake.datasets.equity_index_futures`，目前没有可 import implementation。固定操作如下，semantic_request 是待决 Scope/Window 的概念占位，不是已发布 Python type：

| Operation | Stable contract |
| --- | --- |
| coverage(semantic_request) → CoverageResult | 查询已确认目标 units 的缓存完整性；无 Source I/O、无 mutation、不隐式 ensure |
| ensure(semantic_request) → EnsureResult | 只执行 missing/non-success units，已有 success 默认跳过；逐 unit completeness/原子提交 |
| export(semantic_request) → Futures Market Facts View | Dataset-owned business view，遵循公共 Export Envelope；无 Source I/O、无 mutation、不负责文件交付 |

不增加 sync/read/daily-update verbs，不要求 DataLake manager/registry，也不让 caller 提供 SQLite path、Repository、Source adapter、token 或 FetchUnit persistence identity。Concrete service/factory/request types 在 domain decisions 完成后编码；不以签名占位迫使后续设计采用 contract × date。

Coverage/ensure 的公共 fields、互斥状态计数、complete 含义、failure taxonomy 与默认 success freshness 继承公共 authority。UnitFailure 必须使用最终确认的 semantic FetchUnit identity，不使用 unit_id；本轮不定义 requested_units、records_written 的 Dataset-specific 公式或 failure identity shape。

## 2. 已锁定 export boundary

Export envelope 必须包含 dataset（固定 `equity_index_futures`）、view、export_schema_version、scope、window、coverage 与 owning Dataset business payload。Business view 应能表达合约 identity/product、交割/到期、exchange/lifecycle、underlying semantic identity 及本 Dataset 的 Source market facts；不输出 generic SQLite dump。

Payload 只包含最终 Scope/Window 内成功 units 的合法 cached facts；incomplete coverage 可返回当前可用 facts 与准确 coverage，无可用事实时返回明确 empty payload。Coverage 与 payload 来自同一个 committed owned-cache snapshot。禁止 SQLite path、unit/record IDs、Repository、provider response object 与 transport metadata。

不在此 view 计算 basis、term structure、premium、rolling features 或 research statistics，不跨 Dataset 读取/join internal state。Underlying identity 只是 relationship fact，不保证 Index Dataset 已缓存对应行情，也不授予 runtime dependency。

## 3. 尚待人工决定的 consumer details

Domain 待决项唯一 owner 为 ARCHITECTURE.md 第 3 节；它们解决之后，本 SERVICE 才能固定以下 details：

- Concrete semantic request fields/types、normalization 与 validation；Window interpretation、目标展开与 boundary cases。
- Semantic unit failure identity、逐 unit completeness 对结果 accounting 的 specialization。
- View identity、export_schema_version 的首次发布、payload 名称/shape、required facts、types、units、ordering 与 empty representation。
- Provider runtime composition / credential convention（复用 repository 已有约定）、factory 与 public facade 概念。

本轮没有未决项目的隐式 default；不能将未知 contracts 当作空范围后返回 complete=true。没有新增 Source/Calendar dependency permission。InvalidRequestError、OperationError 与可恢复 unit failure 使用公共分类，不发明新的 transport error；未定的业务 request validation 不由 Agent 先实现。
