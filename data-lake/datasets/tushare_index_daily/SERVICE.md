# tushare_index_daily Public Application Service authority

本文件拥有 Index Dataset 的 transport-neutral public request/result/view 与 runtime contract，继承 [Dataset domain](ARCHITECTURE.md) 及公共 [APPLICATION.md](../../APPLICATION.md)。Facts/Instrument 由 [FACTS.md](FACTS.md) 拥有，Calendar prerequisite 由 [TRADING_DAYS.md](TRADING_DAYS.md) 拥有；不定义 CLI flags、HTTP DTO 或 SQLite schema。

## 1. Public Python surface

Canonical namespace 为 `data_lake.datasets.tushare_index_daily`，发布 `IndexDailyService`、`IndexDailyRange`、`IndexDailyRow`、`IndexDailyExport` 与 `create_service()`。这些是稳定 consumer contract。公共 CoverageResult / EnsureResult / UnitFailure / errors 复用 DataLake contract。

```text
coverage(request: IndexDailyRange) → CoverageResult
ensure(request: IndexDailyRange)   → EnsureResult
export(request: IndexDailyRange)   → IndexDailyExport
```

Consumer 通过 public semantic objects 直接使用 service，不经 CLI/JSON round-trip，也不接收 SQLite path、Repository、Source adapter、connection 或 provider response。Factory 由 Dataset 内部 composition 解析 owned state 及 Calendar public service；普通 consumer 不需要配置 internal collaborators。Factory/read-only calls 不创建缓存，不要求 credential。

行情 Window 的 end_date 必须不晚于 operation 验证时的 Asia/Shanghai 当前日期；未来结束日期在任何 dependency/Source I/O 前抛 InvalidRequestError，不截断日期。当天未发布仍按完整性失败保持可重试。Calendar 继续允许已发布的未来日期。

## 2. Shared semantic request

| IndexDailyRange field | Python semantic type | Meaning |
| --- | --- | --- |
| index_codes | 非空 str sequence，不能是单个 str | 显式完整 Source codes；按 FACTS.md 解释为 canonical set |
| start_date | datetime.date，非 datetime timestamp | inclusive lower bound |
| end_date | datetime.date，非 datetime timestamp | inclusive upper bound，start_date <= end_date |

不使用裸 symbol、名称、隐式指数 defaults 或 today default；不 trim/改写 codes，不交换日期。空输入、错误 semantic types、非 canonical code representation 或倒置范围属于 InvalidRequestError，在任何 dependency/Source 操作前验证。Source membership 不为 read-only validation 额外请求；只有 selected units 的 ensure 需要确认尚未缓存的合法 instrument metadata。

Scope 为 canonical sorted unique index_codes，Window 为 request 两端 date；caller 不构造 FetchUnits。Credential、filesystem path、output path、argparse namespace 与 HTTP DTO 不属于 semantic input。

## 3. Coverage 与 ensure

Coverage 先按 TRADING_DAYS.md 固定完整交易日集合，再只统计目标 Index units；互斥计数、complete、read-only 与 cache absence 继承公共 Application authority。Index owned cache 缺失且 Calendar 可用时，所有目标 units 为 missing；Calendar 不可用时抛 OperationError，不能估算 requested_units。Complete 只表达成功缓存完整性，不表达 freshness 或 metadata/provider-current 状态。

Ensure 按交易日 prerequisite 契约准备 Calendar 后，只执行 missing / non-success Index units，复用合法 local instrument metadata，必要时调用 index_basic，再由 index_daily 请求/partition 与逐 unit completeness 完成原子写入。Batching/retries 不改写 requested_units 或 attempted_units；已有 success 不重写，不为更新 metadata 单独请求 Source。

Historical initialization 与每日更新使用同一 operation：

```text
ensure(IndexDailyRange(index_codes, historical_start, historical_end))
ensure(IndexDailyRange(index_codes, today, today))
```

Today 由 caller 传入；若当天开市但 Source 尚未发布日线，目标 unit 失败/保持 non-success，不把零行情当 success；后续同一 ensure 可重试。休市日零目标的行为见 TRADING_DAYS.md，不发布独立 daily-update / sync command。

Public result fields 与 accounting 继承公共 Application authority。每个最终 failed attempt 恰有一个 UnitFailure：semantic `identity=(index_code: str, trade_date: date)`，`reason` 为可读字符串。Missing row、duplicate/conflicting identity、非法 facts、metadata failure 或可恢复批请求 failure 按受影响 selected units 记录，其他可验证 units 继续；不能合法 partition 的 response 不得宣告所尝试 units 成功。`records_written = succeeded_units`，不包含 instrument entries、Calendar 写入或已缓存 Index records；所有 Index counters 只统计 Index units。

## 4. Index Daily business view

V1 唯一 view identity 为 `index_daily`，没有 view selector。IndexDailyExport 遵循公共 Export Envelope：

| Field | Semantic value / type |
| --- | --- |
| dataset | str，固定 `tushare_index_daily` |
| view | str，固定 `index_daily` |
| export_schema_version | int，固定 1，不是 SQLite schema_version |
| scope | IndexDailyScope，字段 index_codes 为 canonical sorted unique selection |
| window | start_date / end_date 为 request 对应 date |
| coverage | 固定交易日目标的 CoverageResult |
| records | IndexDailyRow sequence，按 (index_code, trade_date) ascending |

IndexDailyRow 是 business-oriented projection，不是 Repository Record dump，具有以下 public fields：

| Fields | Python semantic types / meaning |
| --- | --- |
| index_code, symbol, name, market | str，本地合法 instrument identity/metadata |
| publisher, category | str 或 None，Source 合法缺席 |
| trade_date | datetime.date |
| open, high, low, close, pre_close, change, pct_change, volume, amount | finite float，Source meaning 与单位严格继承 FACTS.md |

Metadata 表达 export snapshot 中的 cached instrument facts，不宣称是 trade_date 当时的历史 metadata。Envelope 的 export_schema_version 只对该 view 定义；不受 internal SQL column names 影响。

只导出该 selection/Window 及固定交易日集合内 success units 的合法事实。`len(records) = coverage.successful_units`；无成功 units 时为空序列，不补齐缺失行情，不导出 failed/pending 残留。Calendar 可用但 Index incomplete 时合法返回部分 view、coverage.complete=false；Calendar 不完整时整个 export 失败。Coverage、records 与关联 instrument metadata 来自同一个 Index committed snapshot，不能拼接不同缓存状态。

不暴露 SQLite path、unit_id/unit_key、record_id、content_hash、Repository、provider response 或 transport metadata，不添加 derived indicators。Export 不写文件；CLI/HTTP adapter 仅拥有 serialization/delivery。稳定 wire meaning：date → YYYY-MM-DD，None → null，scope.index_codes/records → ordered arrays，float → finite JSON numbers，coverage counters → integers，complete → boolean；单位不随序列化转换。

## 5. Failures、runtime 与实现边界

InvalidRequestError / OperationError 的唯一公共 owner 为 APPLICATION.md。自身 request validation failure 为 InvalidRequestError；storage/integrity/execution/credential failure 为 OperationError；Calendar prerequisite failure 按 TRADING_DAYS.md 映射为 OperationError；可恢复 Index unit failures 为 EnsureResult.failures，不新增第三类公共 error。

Tushare execution 遵循 [Provider Runtime authority](../../providers/TUSHARE.md)，factory 与整个 operation 调用链继承公共 lazy Source I/O invariant；Calendar prerequisite 是否需要 Source I/O 由 TRADING_DAYS.md 拥有。

本 Dataset 自己的 composition 拥有 index_basic/index_daily adapter 与 local storage resolution，adapter 通过共享 Executor 执行 provider 请求；只通过 Calendar public namespace 消费 prerequisite，不读取 sibling persistence。SQLite lifecycle、默认 filename convention、旧目录 state 隔离与 rebuild-only compatibility 继承 [PERSISTENCE.md](../../PERSISTENCE.md)；bounded Source execution 见下节。Consumer integration 与 deferred semantics 继承模块架构。

## Bounded Source execution

同一 index_code 和自然年内每批最多 250 个 selected 交易日，使用 index_daily 的 start_date/end_date 查询并完整分页。只提交本次 selected units，逐 unit completeness 与 public accounting 不变。执行、验证复用及单 worker 提前一批见 [EXECUTION.md](../../EXECUTION.md)。
