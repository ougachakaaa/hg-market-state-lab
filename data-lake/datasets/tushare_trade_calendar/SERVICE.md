# tushare_trade_calendar Public Application Service authority

本文件拥有 Dataset-specific public semantic request/result/view、Python consumption、failures specialization、runtime/source credential 与 serialization 边界。继承 [Dataset domain](ARCHITECTURE.md) 与公共 [APPLICATION.md](../../APPLICATION.md)。不定义 CLI option names、HTTP endpoints、HTTP status codes 或存储实现。

## 1. Canonical service 与 Python boundary

Canonical public Python surface 属于 `data_lake.datasets.tushare_trade_calendar`，至少发布以下概念：

```text
TradeCalendarService
TradeCalendarRange
TradeCalendarRecord
TradeCalendarExport
create_service()
```

Public operations 为：

```text
coverage(request: TradeCalendarRange) → CoverageResult
ensure(request: TradeCalendarRange)   → EnsureResult
export(request: TradeCalendarRange)   → TradeCalendarExport
```

```text
lab CLI / future HTTP API / Research / Snapshot-Preparation / Python consumers
    ↓
data_lake.datasets.tushare_trade_calendar Public Application Service
    ↓
internal Source Adapter / Repository / SQLite
```

这是 canonical consumer boundary，不依赖 CLI / HTTP。Consumer 不访问 SQLite、Repository、Source adapter 或 Tushare transport response，也不通过 CLI 或反向解析 JSON 获取 Python result。实际 Research / Snapshot integration 仍须独立设计，不因 boundary 发布而宣称已接入。

普通 consumer 使用 `create_service()` 创建 service，不要求显式传入 SQLite path、Repository、Source Adapter、database connection 或 `TUSHARE_TOKEN`。Runtime/storage/source configuration 由 DataLake 内部拥有。Factory 本身不要求 Source credential，不为了后续 read-only operation 创建缓存。

`CoverageResult`、`EnsureResult`、`UnitFailure` 与两类 application errors 继承公共 Application authority，可由公共 `data_lake` facade 提供；caller 必须能消费结果并识别错误，无需访问 internals。内部文件拆分、类型载体与共享类型 re-export 方式留给 implementation，不改变 public semantics。

以下为目标消费示意，不声明已实现：

```python
from datetime import date
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service

service = create_service()
request = TradeCalendarRange(
    exchange="SSE", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
)
coverage = service.coverage(request)
result = service.ensure(request)
view = service.export(request)
```

## 2. Common semantic request

三个 operation 共享 `TradeCalendarRange`：

| 字段 | Public Python semantic type | 约束 |
| --- | --- | --- |
| exchange | str | 必填、非空的 provider-native canonical identifier，无 provider default |
| start_date | date | 必填，inclusive lower bound |
| end_date | date | 必填，inclusive upper bound，start_date <= end_date |

日期是 Python `datetime.date`，不是 raw strings 或 datetime timestamps。Exchange 不猜测、不改写大小写或建立本地 enum；空白或含首尾空白的输入不是 canonical identifier，不通过 trim 后替换输入。Provider 支持哪些 canonical identifiers 由 Source 决定，不为 request validation 额外访问 Source。

错误 semantic types、缺失值与无效 range 属于 `InvalidRequestError`，不能自动交换日期。Scope / Window expansion 是内部 domain interpretation；caller 只表达 range，无需构造 FetchUnits 或理解 persistence mechanics。Credential、SQLite path、output path、argparse namespace 与 HTTP DTO 不属于 request。

## 3. Coverage 与 ensure specialization

结果字段、互斥计数、complete 与不存在缓存的处理继承 [APPLICATION.md](../../APPLICATION.md)。本 Dataset 的 `requested_units = (end_date - start_date).days + 1`，包括休市日。Coverage 是 cache completeness，不表达 freshness。

Ensure 使用 Tushare `trade_cal`，Source 请求显式指定目标 exchange。Batching 不改变 [domain completeness](ARCHITECTURE.md)；返回 facts 按 identity partition。已有 success units 跳过，即使 batch response 包含它们也不重写。每个 selected unit 独立验证并原子提交。

缺失目标日期、duplicate / conflicting identity、目标 identity 不匹配、非法 normalization 或 completeness failure 按受影响 unit 返回 failure，其他可完整验证 units 继续尽可能写入。外来 identity 不能替代目标 unit，也不能写入目标之外的 units。可恢复的 Source request failure 映射到该请求实际尝试的目标 units；不能确定合法目标归属的 Source response 不得用于宣告所尝试 units 成功。

`EnsureResult.failures` 每项使用公共 `UnitFailure` 语义：`identity` 为 `(exchange: str, cal_date: date)`，`reason` 为可读字符串；每个最终 failed attempt 恰有一项，不使用 persistence ID 或 transport response。`records_written = succeeded_units`，因为每个成功 unit exactly owns one Record。Complete 仍按操作结束后的 coverage 决定。不可执行的整个 operation 按下文抛 application failure。

## 4. TradeCalendarRecord 与 semantic export view

`export` 构造 Dataset-owned business view，可被 Python caller 直接消费，不写文件、不接收 output path、不隐式 ensure。V1 唯一 view 为 `calendar`，不引入 view selector。

`TradeCalendarRecord` 恰有四个 public semantic fields：

| 字段 | Public Python semantic type |
| --- | --- |
| exchange | str |
| cal_date | date |
| is_open | int，值为 0 或 1，不是 bool |
| pretrade_date | date 或 None |

Facts 合法性与 Source 合法缺席由 [Dataset domain](ARCHITECTURE.md) 拥有；`None` 只表达该合法缺席。Internal persistence fields 不进入 Record。

`TradeCalendarExport` 至少拥有以下 semantic fields：

| 字段 | Semantic value / type |
| --- | --- |
| dataset | str，固定 `tushare_trade_calendar` |
| view | str，固定 `calendar` |
| export_schema_version | int，固定 `1`，不是 SQLite schema version |
| scope | TradeCalendarScope，exchange 等于 request.exchange |
| window | 日期范围值，start_date / end_date 为 request 对应的 date |
| coverage | CoverageResult，针对该 request |
| records | TradeCalendarRecord 有序序列，按 cal_date ascending |

Scope 与 window 是 view context，caller 不必预先构造它们；Python 容器类型留给 implementation，但其字段与值必须可直接消费，不能要求 caller 解析 JSON。

Records 只包含目标 exchange / inclusive range 内成功 units 的合法 facts，包括休市日，不增加 is_open filter，不补齐缺失日期。每个成功 unit 对应一条 Record，因此 `len(records) = coverage.successful_units`；无成功 facts 时为空序列。Incomplete coverage 仍是合法 view。

Coverage 与 records 必须来自公共 Application authority 定义的同一个逻辑 committed cache snapshot，不能由不同缓存状态的读取拼接。本 view 不包含 unit_key、content_hash、SQLite metadata、internal IDs 或 provider transport metadata。

## 5. Semantic objects 与 wire meaning

Service 返回 semantic objects，JSON 只是一种 adapter representation。稳定 JSON meaning 为：日期成为 `YYYY-MM-DD`；`None` 成为 `null`；`is_open` 成为 integer 0 / 1；coverage 计数为 JSON integers、complete 为 boolean；records 成为有序 array。Scope 表达 `{exchange}`，window 表达 `{start_date, end_date}`，envelope / Record 字段名与上述 contract 一致。

Serialization 与 delivery 由 adapter 拥有；[lab](../../../lab/ARCHITECTURE.md) 负责 CLI parsing、JSON file delivery 与 exit-code mapping，未来 HTTP adapter 负责自己的 parsing、DTO projection、serialization 与 error mapping。Adapter 不重新决定 Dataset semantics；本文件不设计 HTTP endpoint 或固定 HTTP status code。

## 6. Application failures 与 runtime configuration

公共 taxonomy 的唯一 owner 为 [APPLICATION.md](../../APPLICATION.md)：

- `InvalidRequestError`：caller-side semantic validation failure，包括非法日期范围、错误 semantic types、空或无效 exchange 输入。
- `OperationError`：Dataset 无法读取、persistence integrity / execution failure、required credential 缺失、Source operation 无法执行或无法生成合法 view。
- 可恢复的单 FetchUnit failure：进入 `EnsureResult.failures`，不抛整个 operation exception。

Coverage / export 无 Source I/O，不要求 credential。Ensure 只有实际需要 Source I/O 时才解析 credential；全部目标已 success 时无需 token。缺少 required credential 在 Source request 前以 `OperationError` 失败，不伪装成逐 unit 正常失败结果。

复用仓库现有凭据约定：环境变量 `TUSHARE_TOKEN` 优先，本地 `market-snapshot/.env` 仅作 fallback，加载不覆盖已有环境变量。该路径是 runtime configuration convention，不授权 import Snapshot 私有 Source client 或 artifact helper。SQLite location 由 DataLake internal runtime 解析；filesystem root / filename、连接、Source composition 与 transaction implementation 留给实现。

## 7. Implementation reconciliation

本文是目标 authority，未声明 Dataset service、factory、CLI 或 HTTP 已实现。基线 commit 的 core 仅提供公共基础设施；现有 `ApplicationFailure` 尚未区分两类错误，`ExportEnvelope.export_schema_version` 的 string annotation 与本 view 的 integer version 不一致。后续 implementation 必须按公共 Application taxonomy 和本文 public types 显式对齐，不将这些现状作为另一套 canonical semantics；本任务不修改 Python。
