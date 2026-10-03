# CFFEX expiry / DTE retained Artifact contract

本文件拥有 [cffex_option_expiry_dte_chain](ARCHITECTURE.md) 的 Artifact semantic shape、provenance、completeness / publication 与 acceptance。Business identity / population / grain 由 entry 拥有，derived resolution 由 [DATE_RESOLUTION.md](DATE_RESOLUTION.md) 拥有；Python owned-type mapping 见 [IMPLEMENTATION](IMPLEMENTATION.md)；本文件不定义 Python classes、serialization envelope 或 SQLite schema。

## Resolution facts 与 semantic identity

Consumer 必须能够定位 Observation identity、normalized business inputs 与对应 complete retained Artifact，并直接消费以下 resolution facts：

| Fact | Semantic type / relationship |
| --- | --- |
| product_code | canonical str，等于请求产品 |
| expiry_date | date，等于请求 expiry |
| target_dte | 正整数，caller 请求的自然日 DTE |
| ideal_calendar_date | date，由 expiry_date / target_dte 计算的理论日期 |
| observation_date | date，按 date resolution 选定的实际 CFFEX 开市日 |
| actual_dte | 正整数，由 expiry_date / observation_date 计算，可能大于 target_dte |

上述事实不是 execution metadata。不能把 observation_date 写为理论日期，或把 actual_dte 写成请求值；business key 不包含这两个 derived facts。

## Market facts

Artifact 承载 [entry population](ARCHITECTURE.md#population-与-grain) 的全部 matching public rows，每条 row 保留完整 [OptionsDailyRow public field contract](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md#3-options-daily-export-v2)：

- Contract / market identity：contract_code、product_code、symbol、name、exchange、source_underlying_code、underlying_index_code。
- Contract metadata：option_type、exercise_type、quote_unit、settlement_month、call_put、per_unit、opt_multiplier、strike、list_date、delist_date、expiry、last_exercise_date、last_delivery_date。
- Daily facts：trade_date、pre_close、pre_settle、open、high、low、close、settle、volume、amount、open_interest。

保留 upstream values、semantic types、排序 `(product_code, trade_date, contract_code)` 与合法 None；字段 meaning、单位、required / nullable rules 唯一归属 [Options FACTS.md](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md)。特别是 per_unit 与 opt_multiplier 不合并；amount 不换算；上市首日 pre_close=None、合法零成交时 open/high/low 的个别 None、last_delivery_date 的合法缺席均照原值保留。不补零、不前值填充、不 rounding，不新增 Greeks、IV、moneyness、收益或统计指标。

所有 rows 必须满足 product_code=request.product_code、expiry=expiry_date、trade_date=observation_date；同一 contract 恰有一条 row。没有额外 strike / CALL-PUT filter，不要求构造人工配对；完整性以 upstream 已证明的真实 contract universe 为准，不以偶数行数、CALL/PUT 数量相等或行情数量猜测。

## Required provenance 与 limitations

保留用于最终 date resolution 与选定 product-day 的 public context：

- Calendar：dataset=`tushare_trade_calendar`、view=`calendar`、export_schema_version、scope.exchange=`CFFEX`、所消费的 window 与 complete coverage context，足以解释所用开市事实。
- Options：dataset=`tushare_equity_index_options`、view=`options_daily`、export_schema_version、scope.product_codes 仅含请求产品、window.start_date=window.end_date=observation_date，以及该 export 的 complete coverage context。

Context 来自实际使用的 public exports，保持 Calendar / Options 各自 snapshot 与 coverage 的含义；不声称两库共享 snapshot 或 provider-current freshness。Market metadata 来自 Options 成功时保留的合法 facts，不重新查询最新 catalog 替换历史成功依据。

本 contract 不要求 execution timestamp、UUID、source digest、code hash、全回溯审计日志或 internal completeness basis。Internal IDs / unit keys、content hashes、SQLite path、Repository objects、provider responses / transport metadata 不进入 Artifact。Provenance 与 business identity 分开，不决定 refresh 或 generation history。

## Completeness 与 publication

只有以下 invariants 全部满足，Artifact 才能发布为 complete：

1. 三个 inputs 合法，normalized business key 与 entry 一致。
2. ideal_calendar_date 按 canonical 公式可确定计算。
3. observation_date 按完整 Calendar facts 与 candidate 回溯规则解析，没有因 upstream failure 跳日。
4. 选定 product-day 的 Options public export 被证明 complete，coverage 与 rows 属于同一 committed snapshot。
5. requested expiry 存在至少一条合法 matching contract row。
6. matching population 全部且恰好纳入 Artifact，没有排除、补造或重复 contract。
7. actual_dte 与日期公式一致，actual_dte>=target_dte；row identities 与 resolution facts 一致。
8. Resolution facts、market facts 与 required provenance 形成一致的 retained Artifact。
9. 依照 [framework completion visibility](../ARCHITECTURE.md#completeness-与-public-boundary)，只有 complete Artifact 可见并满足 business key。

Partial persistence、interrupted / failed execution 不可作为 complete 返回。失败可以留下 framework 允许的 internal unfinished state，但不能使 consumer 看到可消费的空/部分 Artifact；已有成功 upstream commits 不因此获得跨库 rollback 保证。具体 SQLite transaction、locking、retry 或内部 state machine 不在本轮决定。

## Acceptance scenarios

以下是 semantic acceptance；producer executable checks 与 durable reuse criteria 见 [framework IMPLEMENTATION](../IMPLEMENTATION.md#implementation-acceptance-与-handoff)：

| Scenario | Required outcome |
| --- | --- |
| expiry=2026-10-23、target_dte=15 | 理论日期为 2026-10-09；若该日被证明开市且有完整 matching chain，则 actual_dte=15。 |
| target_dte=1 | 理论日期等于 expiry；若需回溯，则 actual_dte>1，不重写 target_dte。 |
| 理论日期为周末 / 假日 | 按完整 CFFEX Calendar 选最近更早开市日，actual_dte 正确增大；不按 weekday 猜测。 |
| 最近 candidate complete，但 requested expiry 不存在 | 继续向前一开市日；保留首次非空完整 matching chain。 |
| candidate cache missing | 必要时 ensure；补齐后有 matching chain 则使用该日，不因 cache missing 回退。 |
| 已证明空 product-day | 允许继续回溯，不发布 empty Observation。 |
| Calendar / Options ensure incomplete、UnitFailure、credential / operation / integrity failure 或非法 view | invocation 失败，不继续 fallback、不满足 key。 |
| 合法首日 pre_close=None / 零成交 nullable OHLC / last_delivery_date=None | 保留该 contract 原始合法值，不排除、不填补。 |
| 完整 matching population | 全部真实 strikes、CALL/PUT 纳入，grain / uniqueness / ordering 正确，无 Study filters。 |
| complete Artifact 已存在 | 相同有效 definition 与 key 直接复用，零 upstream access / computation，无第二个逻辑 Artifact；不要求 upstream 此时仍可用。 |
| 无 complete Artifact / 执行中断 / 发布失败 | key 未满足；consumer 无法消费 unfinished state，后续 invocation 不将其当 complete hit。 |
| 非法 inputs / 日期计算溢出 / 无法继续回溯 | 明确失败，不产生 complete Artifact，不引入默认值或人为历史下界。 |
| 多个 Study 消费同一 Artifact | Artifact 可复用；Study 不读取 SQLite，也不把自己的 Evidence lifecycle 用于 overwrite Artifact。 |

验收同时核对 [entry persistence boundary](ARCHITECTURE.md#persistence-ownership) 与十三个 [Schema areas](../SCHEMA.md#required-semantic-areas)。本 contract 不包含 Analysis、Evidence、Study conclusions 或跨 expiry composition。
