# tushare_equity_index_futures Public Application Service authority

本文件拥有 transport-neutral public request/result/view 与 runtime contract，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [APPLICATION.md](../../APPLICATION.md)。Source facts 由 [FACTS.md](FACTS.md) 拥有，strong completeness 由 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md) 拥有，Calendar prerequisite 见 [TRADING_DAYS.md](TRADING_DAYS.md)。不定义 CLI flags、HTTP DTO 或 SQL。

六角色绑定、Composition Root 与目标内部职责组织由 [Dataset architecture](ARCHITECTURE.md) 拥有，并继承公共 [COMPOSITION.md](../../COMPOSITION.md)；本文件只拥有 consumer contract 与 operation specialization。

## 1. Public Python surface 与 request

Canonical namespace 为 `data_lake.datasets.tushare_equity_index_futures`，发布 `FuturesDailyService`、`FuturesDailyRange`、`FuturesDailyRow`、`FuturesDailyExport` 与 `create_service()`。公共 CoverageResult、EnsureResult、UnitFailure 和 errors 复用 DataLake contract。

```text
coverage(request: FuturesDailyRange) → CoverageResult
ensure(request: FuturesDailyRange)   → EnsureResult
export(request: FuturesDailyRange)   → FuturesDailyExport
```

| FuturesDailyRange field | Python semantic type / meaning |
| --- | --- |
| product_codes | 非空 sequence[str]，不接受单个 str；canonical uppercase ASCII 产品代码，当前 IF/IH/IC/IM，classification 见 FACTS.md |
| start_date | datetime.date，拒绝 datetime timestamp；inclusive |
| end_date | datetime.date，拒绝 datetime timestamp；inclusive，start_date <= end_date |

Product selection 解释为 sorted unique canonical set；不 trim、转大小写、名称猜测或隐式 defaults。重复合法代码去重，不是重复 FetchUnits；未在当前市场关系表确认的产品为 InvalidRequestError，未来扩展按 FACTS.md。空/错误 types、非法代码或倒置范围在任何 dependency/Source 操作前 InvalidRequestError，不交换日期。Request 不接受 contract、delivery month、token、path、output path 或 internal object；Scope 只含 product_codes，Window 为两端 date。

Consumer 调用、factory 与 read-only boundary 继承 [APPLICATION.md](../../APPLICATION.md)。`create_service()` 由本 Dataset 内部 composition 组合 owned storage、fut_basic/fut_daily adapter、必要的 type-2 exclusion 获取与 Calendar public service。

行情 Window 的 end_date 必须不晚于 operation 验证时的 Asia/Shanghai 当前日期；未来结束日期在任何 dependency/Source I/O 前抛 InvalidRequestError，不截断日期。当天未发布仍按完整性失败保持可重试。Calendar 继续允许已发布的未来日期。

## 2. Coverage、ensure 与 accounting

按 TRADING_DAYS.md 固定完整 CFFEX 交易日目标。Coverage 只统计自己目标 product-day units 的 success/missing/pending/failed；互斥计数与 complete 继承 APPLICATION.md。Calendar 可用、owned cache 不存在时目标全 missing；Calendar 不可用时 OperationError，不能估算目标。Complete 只表达缓存 completeness。

Ensure 仅尝试 missing/non-success 目标，已有 success 跳过；有 attempts 时每次重新取得完整 metadata catalog 并冻结，逐 product-day 验证 expected/observed 和全部 required facts，原子成功遵循 CONTRACT_UNIVERSE.md。全 success/零目标时不调用 metadata/daily；Calendar 只有 incomplete 时允许 prerequisite ensure。Source batching/retries 不改变 unit identity 或计数。

| EnsureResult field | Futures specialization |
| --- | --- |
| requested_units / already_successful_units | 目标 product-day 数 / 调用开始时跳过的 success 数 |
| attempted_units | 本次尝试的不同 product-day 数，不是 Source requests 或合约数 |
| succeeded_units / failed_units | attempts 的最终成功 / 失败 product-day 数，两者和为 attempted_units |
| records_written | 本次成功原子提交的 contract-day Records 数，不含 instrument/catalog metadata、Calendar writes、失败残留或已有成功 Records |
| complete / failures | 结束时目标 coverage.complete / 每个最终 failed attempt 恰一项 UnitFailure |

UnitFailure 的 semantic identity 为 `(product_code: str, trade_date: datetime.date)`，reason 为可读 str，不含 persistence IDs。一个成功 product-day 可写多条或已证明为空时零条 Records；不存在 records_written == succeeded_units 的 invariant。Catalog proof/可恢复 metadata 或 daily failure 按受影响目标编码 UnitFailure，其他可验证 units 继续；不能合法 partition 时受影响 units 全部失败。无效 input 为 InvalidRequestError；缺必需 credential、cache integrity/读写失败或无法执行整个 operation 为 OperationError，不伪装正常结果。Calendar prerequisite 未知目标时按 TRADING_DAYS.md 整个 operation 失败。

Historical initialization 与 daily update 使用同一 ensure，caller 显式给日期：`ensure(FuturesDailyRange(product_codes, historical_start, historical_end))` 或 start_date=end_date 的当天请求。开市但日行情未发布时 unit non-success，后续同一 ensure 可重试；休市时零目标。无新增 refresh、daily-update、sync 或 force verbs。

## 3. Futures Daily Export V2

唯一 view 为 `futures_daily`，无 selector。FuturesDailyExport 的 envelope：

| Field | Python semantic value / type |
| --- | --- |
| dataset | str，固定 tushare_equity_index_futures |
| view / export_schema_version | str futures_daily / int 2；不等于 SQLite schema version |
| scope | FuturesDailyScope，product_codes 为 sorted unique product sequence |
| window | start_date / end_date 为 request 对应 datetime.date |
| coverage | 固定目标的 CoverageResult |
| records | 扁平 FuturesDailyRow sequence，按 (product_code, trade_date, contract_code) ascending |

FuturesDailyRow 合并该成功 unit 保留的合法 Instrument facts 与 daily facts，全部 public fields/types 如下；mapping、单位与 required/nullable rules 由 FACTS.md 唯一拥有：

| Fields | Python semantic type |
| --- | --- |
| contract_code, product_code, symbol, name, exchange, underlying_index_code | str |
| trade_unit, quote_unit, delivery_month | str；delivery_month 为 YYYYMM |
| multiplier, per_unit | finite positive float |
| list_date, delist_date, last_delivery_date, trade_date | datetime.date |
| pre_close | finite float 或 None；仅上市首日 Source 合法缺席 |
| pre_settle, open, high, low, close, settle | finite float |
| close_change_from_pre_settle, settle_change_from_pre_settle | finite float |
| volume, amount, open_interest | finite float，非负限制按 FACTS.md |
| open_interest_change | finite float 或 None；可负，仅上市首日 Source 合法缺席可为 None |
| delivery_settlement_price | finite float 或 None，仅 Source 合法缺席 |

只包含目标 selection/Window/固定 D 内 success units 的完整 Records；partial coverage 合法返回可用成功 units、complete=false，失败/pending 残留不导出。无成功 Records 时为空序列；成功空 unit 不补造行。Records 数是各成功 unit record count 之和，不要求等于 successful_units。

Coverage、Records 和成功时保留的合法 metadata/completeness basis 来自同一个 Futures committed snapshot；不能使用最新 catalog 回溯替换旧 unit 的依据或拼接不同缓存状态。Calendar 不完整时整个 export OperationError。Metadata 不宣称是 trade_date 当时 metadata，也不保证 freshness。

不暴露 unit_id/unit_key、record_id、hash、SQLite path、Repository、provider response 或 transport metadata，不增加 derived features。Export 不写文件；adapter 拥有 serialization/delivery。稳定 wire meaning：date → YYYY-MM-DD，None → null，scope.product_codes/records → ordered arrays，float → finite JSON numbers，counters → integers，complete → boolean；不转换单位。

## 4. Runtime 与实现边界

Provider execution 继承 [Tushare Provider authority](../../providers/tushare/ARCHITECTURE.md)，storage lifecycle 与 compatibility 继承 [PERSISTENCE.md](../../PERSISTENCE.md)。Calendar 调用链与 Source I/O 条件由 [TRADING_DAYS.md](TRADING_DAYS.md) 拥有；BatchPlanner / Source execution 见 [FACTS.md](FACTS.md)。

兼容当前 persistence contract 的已有缓存，其有限数值保持可读，不改写已成功 facts；public export schema version 不授权读取 incompatible persistence generation。
