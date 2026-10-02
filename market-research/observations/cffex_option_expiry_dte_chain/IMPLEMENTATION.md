# Expiry DTE Chain Implementation Contract

本文件拥有 [semantic entry](ARCHITECTURE.md)、[DATE_RESOLUTION](DATE_RESOLUTION.md) 与 [ARTIFACT](ARTIFACT.md) 到 runnable package 的 mapping。继承 [framework IMPLEMENTATION](../IMPLEMENTATION.md) / [UPSTREAM](../UPSTREAM.md)，不改变公式、population、date fallback 或 completeness。

## Public package 与 request

Canonical package 为 `market_research.observations.cffex_option_expiry_dte_chain`，source 在 `market-research/src/market_research/observations/cffex_option_expiry_dte_chain/`。Public init 发布 ExpiryDteChainRequest、ExpiryDteChainArtifact、ExpiryDteChainRow、ExpiryDteChainService、create_service。Public contract、orchestration、date-resolution / deterministic projection、owned persistence 可辨认，private filenames 不锁定。

```python
from datetime import date
from market_research.observations.cffex_option_expiry_dte_chain import (
    ExpiryDteChainRequest, create_service,
)

artifact = create_service().ensure(ExpiryDteChainRequest(
    product_code="IO", expiry_date=date(2026, 10, 23), target_dte=15,
))
```

示例表达 public boundary；市场数据可用性仍依 required public proof 判定。`ExpiryDteChainService.ensure(request: ExpiryDteChainRequest) -> ExpiryDteChainArtifact` 是唯一 public semantic operation。Request 全部必填：product_code: str、expiry_date: datetime.date、target_dte: int；canonical domain、拒绝 timestamps / bool / defaults 等规则引用 entry。

## Owned Artifact、row 与 provenance mapping

| Artifact field | Python semantic type / mapping |
| --- | --- |
| observation_identity | str，固定 cffex_option_expiry_dte_chain |
| product_code / expiry_date / target_dte | str / date / int，与 normalized request 相同 |
| ideal_calendar_date / observation_date / actual_dte | date / date / int，引用 DATE_RESOLUTION 六个 resolution facts |
| rows | immutable ordered sequence[ExpiryDteChainRow]，完整非空 matching population，保留 upstream ordering |
| calendar_provenance | immutable ordered sequence[Observation-owned context values]，按实际用于证明最终 resolution 的 Calendar windows 消费顺序保留；不是全回溯执行审计日志 |
| options_provenance | Observation-owned context value，最终 selected product-day 的实际 export context |
| complete | bool，固定 True，仅 complete 可 return |

Read-only `semantic_identity = (observation_identity, product_code, expiry_date, target_dte)`，不含 derived dates 或 provenance。All values / nested containers immutable，equality 遵循 framework。Rows 是 Observation-owned types；以下全部 fields 原值投影，自身不重新定义单位 / nullable rules：

| ExpiryDteChainRow fields | Python semantic types，引用 [Options SERVICE](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md#3-options-daily-export-v2) |
| --- | --- |
| contract_code, product_code, symbol, name, exchange, source_underlying_code, underlying_index_code, option_type, exercise_type, quote_unit, settlement_month, call_put | str |
| per_unit, opt_multiplier, strike, pre_settle, close, settle, volume, amount, open_interest | float，finite / positive / non-negative constraints 按 upstream fields 各自语义 |
| list_date, delist_date, expiry, last_exercise_date, trade_date | datetime.date |
| last_delivery_date | date 或 None |
| pre_close, open, high, low | float 或 None，仅 upstream 合法 nullable contexts |

Row 值 meanings 唯一引用 [FACTS](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md)，保留完整 ARTIFACT facts / sorting / None，不补零、不 fill、rounding 或单位转换；public annotation / carrier 不使用 OptionsDailyRow。Study 只需理解 ExpiryDteChainRow。

每个 provenance context 的 public field paths：dataset: str、view: str、export_schema_version: int、window.start_date / end_date: date、coverage.requested_units / successful_units / missing_units / pending_units / failed_units: int、coverage.complete: bool。Calendar context 另有 scope.exchange: str 固定 CFFEX；Options context 另有 scope.product_codes: immutable sequence[str] 仅 requested product。它们是 concrete Observation-owned immutable semantic values，carrier names 可由实现选择；不包含 TradeCalendarExport / OptionsDailyExport / CoverageResult 等 runtime objects。

全部 context 从实际完整 exports 无损投影，complete coverage meaning 继承 [DataLake APPLICATION](../../../data-lake/APPLICATION.md)。Calendar windows 足以证明没有跳过更近 candidate；Options window 两端等于 observation_date。分段 Calendar proof 不宣称跨 Dataset / 跨 calls 共享 snapshot，也不新增 source digest / timestamp / UUID / private basis / SQLite path。Calendar records 只用于内部 resolution，不成为 consumer upstream object。

## Factory、owned storage 与 dependencies

无参 create_service 延迟 dependency operation 至 complete miss。Owned SQLite 固定 `market-research/observations/cffex_option_expiry_dte_chain/data/cffex_option_expiry_dte_chain.sqlite3`，普通 consumer 不传 path。Internal composition 只用 `data_lake.datasets.tushare_trade_calendar` 的 TradeCalendarRange / public service，及 `data_lake.datasets.tushare_equity_index_options` 的 OptionsDailyRange / public service；共同 errors 从合法 public facade handling 后映射为 Observation taxonomy。没有 Snapshot adapter / direct Tushare / private provider path。

## Canonical execution mapping

1. 验证 Request / canonical domains，derive normalized business key，lookup owned SQLite；complete hit 直接 return，零 upstream factory / coverage / ensure / export / recomputation。
2. Miss 才计算 ideal_calendar_date；合法 request 的计算溢出为 ObservationOperationError。显式 CFFEX，依 DATE_RESOLUTION 按下方 [Calendar read-first strategy](#calendar-read-first--ensure-if-needed) 取得完整 required window proof。
3. 从完整 Calendar facts 选择 <= ideal date 的最近开市日；休市日不调用 Options。按下方 [Options candidate read-first strategy](#options-candidate-day-read-first--ensure-if-needed) 取得 exact product-day 的完整 export proof。
4. 验证同一 Options export snapshot 的 scope / window / complete / requested_units=successful_units=1 / rows。上游操作失败或非法 view 立即 ObservationOperationError，不跳日期、不换 Snapshot。
5. 恰取全部 row.expiry == request.expiry_date 的 matching rows。只有 complete-but-empty matching population 才继续严格更早的、完整 Calendar 已证明的最近开市日。Cache missing 不证明 absence；任何 required proof 无法继续或日期不可表示即 operation failure，不发布 empty chain。
6. 首个完整非空 matching candidate 定为 observation_date，按已有公式保留 actual_dte；原值投影全部 matching rows / required provenance 为 Observation-owned values，校验 whole Artifact completeness / identities / unique contracts / ordering，然后 atomic publish、return。

Calendar windows / chunks、渐进向历史扩张、batching 是 private mechanics，不锁 chunk 大小；必须覆盖每个更近 candidate 的完整证明。不用 weekday、hard-coded holidays、pretrade_date 代替 proof，不设人为历史 cutoff / arbitrary max fallback count。没有跨库 rollback、额外 Study inputs、population filters 或 upstream failure date fallback。

### Calendar read-first / ensure-if-needed

本 Observation 逐步证明哪个 candidate trading day 含 requested expiry chain，不要求一次准备整个大窗口。对于当前 resolution 必需的 Calendar range，构造 `TradeCalendarRange(exchange="CFFEX", start_date=required_start_date, end_date=required_end_date)`，采用 read-first / ensure-if-needed：

```text
export(required calendar range) / read-only completeness check
    ├── complete → validate / consume this public export
    └── incomplete → ensure(the same required range)
                   → require ensure complete / no failures
                   → export(the same required range)
                   → require complete / validate / consume
```

独立 `coverage()` 可选，不要求 mechanical coverage → ensure → export。最终消费的 records 与 completeness proof 必须来自同一合法 [TradeCalendarExport](../../../data-lake/datasets/tushare_trade_calendar/SERVICE.md#4-tradecalendarrecord-与-semantic-export-view)：dataset=tushare_trade_calendar、view=calendar、schema=1、scope.exchange=CFFEX、window 等于 required range，coverage counters 一致且 complete，每自然日恰一合法 Record。Check 已证明 complete 时不 ensure；当前 export incomplete 才补齐，ensure incomplete / failure 或后续 export incomplete / invalid 均为 ObservationOperationError。

All calendar facts required to prove the nearest valid CFFEX open candidate must be complete。Chunking、window expansion / batching 继续属于 private mechanics；每份 used export 自己提供 committed snapshot proof，不将独立 coverage 与另一份 records 拼接，也不声称不同 Calendar exports / Options 共享 snapshot。

### Options candidate-day read-first / ensure-if-needed

对 Calendar 已证明的 candidate，构造 `OptionsDailyRange(product_codes=(request.product_code,), start_date=candidate, end_date=candidate)`：

```text
read current public completeness / export state for exact product-day
    ├── complete → validate / consume one complete export
    └── missing / pending / failed / incomplete
                   → ensure(exact product-day)
                   → require ensure complete / no failures
                   → export(exact same product-day)
                   → require complete / validate / consume
```

Read proof 可用 `coverage + export`，或仅使用 export 中的 coverage，具体依 [Options SERVICE](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md)。**Do not mutate if the exact product-day is already publicly proven complete**；独立 coverage 不代替最终 export proof。若 coverage 与后续 export 状态不同，以实际 export 的 completeness / payload 决定能否消费；合法 incomplete export 进入补齐路径，不能拼接旧 proof、当作 absence 或越过 candidate。

最终消费 one complete Options export snapshot，验证 dataset=tushare_equity_index_options、view=options_daily、schema=2、scope 仅含 requested product、window 两端为 candidate、coverage.complete=true、requested_units=successful_units=1、其余 counters=0，以及 public records 合法。EnsureResult.complete=true 不代替该 proof；ensure 后 export incomplete / invalid 仍失败。Options read-only operation 的 Calendar prerequisite failure 是 OperationError，不能伪装为已知目标的 cache missing，也不能绕过 Dataset prerequisite ownership。

### Candidate 三态与停止规则

| State | Meaning / required action |
| --- | --- |
| A — cache incomplete / missing | DataLake 尚不能证明 exact product-day complete，含 missing / pending / failed cache units；ensure exact day → export → re-evaluate。不能用当前 empty / partial rows 解释为 expiry absent。初始 failed cache 可补齐，不等于本次 ensure failure。 |
| B — complete product-day、requested expiry absent | 合法完整 export 的 coverage.complete=true，且全部 `row.expiry == request.expiry_date` matching rows 为空；这才是 proven absence，只有此态允许移到严格更早、完整 Calendar 已证明的最近 CFFEX open day。 |
| C — operation / completeness failure | 本次 ensure incomplete / UnitFailure、credential / provider timeout、Calendar prerequisite failure、persistence / integrity failure、invalid export，或其他 required proof 无法满足；立即 ObservationOperationError，不回溯、不换 Snapshot、不当作空、不 skip candidate。 |

```text
cache missing != proven absence
runtime failure != proven absence
DataLake failure != permission to change candidate date
```

Complete export 的非空 matching population 沿 canonical execution 成功形成 chain。上述三态只区分需补齐、已证明缺席与必须失败，保持 [DATE_RESOLUTION](DATE_RESOLUTION.md#proven-absencecache-missing-与-failure) 的既有日期业务规则；date fallback 不是 infrastructure fallback。

## Verification 与 handoff

Framework 三层 checks 之外，按 [Artifact acceptance](ARTIFACT.md#acceptance-scenarios) 验证精确 DTE、target=1、周末 / 假日、Calendar / Options already-complete 无 ensure、两者 incomplete 后 ensure / exact same request export、complete-but-absent、missing 后 ensure、ensure complete 后 export incomplete / invalid 仍失败、upstream failure 立即停止、无限制回溯的 proof / date termination、actual_dte、全 strikes / CALL-PUT、排序 / uniqueness、合法 nullable facts 与 owned provenance。Complete hit 使用不可用 dependency doubles 仍应 return；Study 不需 import DataLake classes。

Durable-before-return 与 service / process recreation 后 same-request 零 upstream reuse 必须通过 [framework durable reuse acceptance](../IMPLEMENTATION.md#durable-reuse-acceptance)，不以仅同一实例 repeat ensure 替代。

Calendar / Options 已有所需 public runtime surface，无 DataLake / Snapshot capability gap。本 producer **Authority Complete / Dependency Reconciled / Implementation Architecture Complete / Implementation Ready**，runtime **Implemented / Verified**；date-resolution / concrete acceptance、durable restart reuse 与首个 Study runtime dependencies / bindings 已验证，见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md#first-observation-driven-vertical-slice-implementation)。
