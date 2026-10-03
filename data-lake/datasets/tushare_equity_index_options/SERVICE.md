# tushare_equity_index_options Public Application Service authority

本文件拥有 transport-neutral public request/result/view 与 runtime contract，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [APPLICATION.md](../../APPLICATION.md)。Source facts 进入 [FACTS.md](FACTS.md)，strong completeness 进入 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，Calendar prerequisite 进入 [TRADING_DAYS.md](TRADING_DAYS.md)。不定义 CLI flags、HTTP DTO 或 SQL。

## 1. Public Python surface 与 request

Canonical namespace 为 `data_lake.datasets.tushare_equity_index_options`，发布 `OptionsDailyService`、`OptionsDailyRange`、`OptionsDailyRow`、`OptionsDailyExport` 与 `create_service()`。公共 CoverageResult、EnsureResult、UnitFailure 和 errors 复用 DataLake contract。

```text
coverage(request: OptionsDailyRange) → CoverageResult
ensure(request: OptionsDailyRange)   → EnsureResult
export(request: OptionsDailyRange)   → OptionsDailyExport
```

| OptionsDailyRange field | Python semantic type / meaning |
| --- | --- |
| product_codes | 非空 sequence[str]，拒绝单个 str；canonical uppercase ASCII 产品代码，当前 IO/HO/MO，classification 见 FACTS.md |
| start_date | datetime.date，拒绝 datetime timestamp；inclusive |
| end_date | datetime.date，拒绝 datetime timestamp；inclusive，start_date <= end_date |

Selection 为 sorted unique canonical set。重复合法代码去重；不 trim、改大小写、猜名称或提供隐式 defaults。未由当前关系表确认的代码、空/错误 types 或倒置范围，在任何 dependency/Source 操作前 InvalidRequestError；未来产品先按 FACTS.md 扩展关系表。Scope 只含 product_codes，Window 为两端 date；不提供 contract、expiry、strike、CALL-PUT filters，不接受 token、path、output path 或 internal object。

Factory 内部组合 owned cache、Source adapter 与 Calendar public service，普通 consumer 不提供 SQLite path、connection、Repository 或 credential。Factory/coverage/export 不创建 state、不要求 token；consumer 直接使用 public semantic objects，无 CLI/JSON round-trip。

行情 Window 的 end_date 必须不晚于 operation 验证时的 Asia/Shanghai 当前日期；未来结束日期在任何 dependency/Source I/O 前抛 InvalidRequestError，不截断日期。当天未发布仍按完整性失败保持可重试。Calendar 继续允许已发布的未来日期。

## 2. Coverage、ensure 与 accounting

按 TRADING_DAYS.md 固定完整 CFFEX 开市日目标，只统计自己 product-day units。互斥 success/missing/pending/failed 与 complete 继承 APPLICATION.md；Calendar 可用而 owned cache 不存在时目标全 missing，prerequisite 不可用时 OperationError，不能按行情行数估算 requested_units。Complete 不表达 freshness。

Ensure 跳过已有 success，只尝试 missing/non-success。有 attempts 时每次重新取得完整 opt_basic catalog，冻结本次 basis，再逐 product-day 验证完整 active expiry/strike/CALL-PUT contract set 及 required daily facts；原子成功遵循 CONTRACT_UNIVERSE.md。全 success/零目标时不请求 metadata/daily；Calendar 仅 incomplete 时允许 prerequisite ensure。请求批量和重试不决定 unit grain。

| EnsureResult field | Options specialization |
| --- | --- |
| requested_units / already_successful_units | 目标 product-day 数 / 调用开始时跳过的 success 数 |
| attempted_units | 本次尝试的不同 product-day 数，不是 contracts、expiry chains、Source requests 或 retries |
| succeeded_units / failed_units | attempts 最终成功 / 失败 product-day 数，两者和为 attempted_units |
| records_written | 本次成功提交的 contract-day Records 数；不含 metadata、Calendar、失败残留或已有成功 Records |
| complete / failures | 结束时目标 coverage.complete / 每个最终 failed attempt 恰一项 UnitFailure |

UnitFailure identity 为 `(product_code: str, trade_date: datetime.date)`，reason 为可读 str，不暴露 persistence IDs。一个成功 product-day 可写多条或证明为空时零条 Records，不能令 records_written=succeeded_units。Catalog proof/可恢复 metadata、daily request 或逐 contract validation failure 按受影响 units 编码，其他可验证 units 继续；无法合法 partition 不宣告受影响 units 成功。无效输入为 InvalidRequestError；缺 required credential、cache integrity/读写失败或整个 operation 无法执行为 OperationError。Calendar 导致目标未知时整个 operation 失败，不能写 Options UnitFailure 冒充已知目标。

Historical initialization 与 daily update 共用 ensure：caller 给 historical range 或显式 start_date=end_date；无 today default。开市日尚未发布日行情时 non-success，后续同一 ensure 可重试；完整 Calendar 证明休市时零目标。零成交 row 与空 universe 分别按 FACTS.md、CONTRACT_UNIVERSE.md 验证，不新增 refresh、sync、daily-update 或 force verbs。

## 3. Options Daily Export V2

唯一 view 为 `options_daily`，无 selector。OptionsDailyExport envelope：

| Field | Python semantic value / type |
| --- | --- |
| dataset | str，固定 tushare_equity_index_options |
| view / export_schema_version | str options_daily / int 2；不等于 SQLite schema version |
| scope | OptionsDailyScope，product_codes 为 sorted unique product sequence |
| window | start_date / end_date 为 request 对应 datetime.date |
| coverage | 固定目标的 CoverageResult |
| records | 扁平 OptionsDailyRow sequence，按 (product_code, trade_date, contract_code) ascending |

OptionsDailyRow 合并成功时保留的合法 Instrument metadata 与 daily facts；全部 public fields/types 如下，mapping、单位和 required/nullable rules 由 FACTS.md 拥有：

| Fields | Python semantic type |
| --- | --- |
| contract_code, product_code, symbol, name, exchange | str |
| source_underlying_code, underlying_index_code, option_type, exercise_type, quote_unit | str |
| settlement_month | str，YYYYMM |
| call_put | str，CALL 或 PUT |
| per_unit, opt_multiplier, strike | finite positive float |
| list_date, delist_date, expiry, last_exercise_date, trade_date | datetime.date |
| last_delivery_date | datetime.date 或 None，Source 合法缺席 |
| pre_close | finite float 或 None；仅上市首日 Source 合法缺席 |
| pre_settle, close, settle | finite float |
| open, high, low | finite float 或 None；只在 Source volume=amount=0 时允许个别 None，实际零保留 |
| volume, amount, open_interest | finite non-negative float |

只包含目标 selection/Window/固定 D 内成功 units 的完整 Records，partial coverage 合法返回已成功产品日、complete=false；不导出 failed/pending 残留，不补造 chain、价格、missing legs 或零行。无成功 Records 时空序列，已证明空 unit 仍可 success。Records 数是各成功 unit record count 之和，不要求等于 successful_units。

Coverage、Records 和关联成功时保留的合法 metadata/completeness basis 来自同一 Options committed snapshot；不按最新 catalog 重判或替换过去成功依据。Calendar 不完整时整个 export OperationError。Metadata 不宣称 trade_date 当时历史 metadata 或 provider-current freshness。

不含 internal IDs/hash、SQLite path、Repository、provider response/transport metadata 或 derived indicators。Service 不写文件；adapter 拥有 serialization/delivery。Wire meaning：date → YYYY-MM-DD，None → null，scope.product_codes/records → ordered arrays，float → finite JSON numbers，counters → integers，complete → boolean；不转换单位。

## 4. Runtime 与实现边界

Tushare execution 遵循 [Provider Runtime authority](../../providers/TUSHARE.md)，factory 与整个 operation 调用链继承公共 lazy Source I/O invariant；Calendar prerequisite 是否需要 Source I/O 由 TRADING_DAYS.md 拥有。

本 Dataset composition 自有 opt_basic/opt_daily adapter 与 data/ 中唯一 SQLite，adapter 通过共享 Executor 执行 provider 请求，Calendar 只经 public namespace。不增加 Index/Futures runtime dependency。SQLite lifecycle、默认 filename convention、旧目录 state 隔离与 rebuild-only compatibility 继承 [PERSISTENCE.md](../../PERSISTENCE.md)；bounded Source execution 见下节。Consumer integration 与 deferred semantics 继承模块架构。

V2 在 V1 字段基础上允许 pre_close 为 float 或 None，仅限 FACTS 声明的上市首日合法缺席；其他字段及完整性不变。兼容当前 persistence contract 的已有缓存，其有限数值保持可读，不改写已成功 facts；public V1/V2 字段演进不授权读取 incompatible persistence generation。

## Bounded Source execution

按日期排列并合并同窗口所有 selected products，每批最多 3 个 selected 交易日，查询自然日跨度同时不超过 31 日，使用 opt_daily 的 exchange/start_date/end_date 查询并完整分页。只提交本次 selected units，逐 unit completeness 与 public accounting 不变。执行、验证复用及单 worker 提前一批见 [EXECUTION.md](../../EXECUTION.md)。
