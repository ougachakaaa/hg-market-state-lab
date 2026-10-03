# CFFEX expiry / DTE date resolution authority

本文件拥有 [cffex_option_expiry_dte_chain](ARCHITECTURE.md) 的 deterministic derivation、日期解析、validity / missingness、fallback 与 failure semantics。Inputs / key / population 由 entry 拥有；complete Artifact 由 [ARTIFACT.md](ARTIFACT.md) 拥有。

## DTE 与理论日期

DTE 使用自然日，expiry 当天定义为 DTE=1：

```text
DTE(observation_date, expiry_date)
    = (expiry_date - observation_date).days + 1
ideal_calendar_date
    = expiry_date - (target_dte - 1 calendar days)
actual_dte
    = (expiry_date - observation_date).days + 1
```

例如 expiry=2026-10-23、target_dte=15，ideal_calendar_date=2026-10-09。该例只验证日期算术，不断言该日市场数据存在。Target DTE 是 caller 请求，actual DTE 是最终解析结果，不能强制相等。

## Deterministic resolution

Complete Artifact lookup 必须先于 upstream access。只有没有可复用 complete Artifact 才执行以下规则：

1. 合法 inputs 计算 ideal_calendar_date；无法表示计算结果则 invocation 失败。
2. 通过 [Calendar public service](../../../data-lake/datasets/tushare_trade_calendar/SERVICE.md) 查询显式 `exchange="CFFEX"` 的日期事实。需要时 ensure 所查询范围，然后 export；只有 coverage.complete=true 且该范围每个自然日恰有合法 Record 才可用于解析。按完整 facts 的 is_open==1，选择不晚于 ideal_calendar_date 的最近开市日作为 candidate。
3. 对 candidate 构造 [OptionsDailyRange](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md)：product_codes 仅为 requested product，start_date=end_date=candidate。使用 public coverage / export 检查；missing / non-success 时通过 ensure 补齐，然后重新 export。
4. 要求单 product-day complete；export scope / window 与 request 一致，candidate 是已确认的开市日，coverage 的 requested_units=successful_units=1。Coverage 与 records 来自同一 Options committed export snapshot；不能拼接先前 coverage 与后续 rows 作为完整证明。
5. 从完整 product-day 的 public rows 选择全部 requested expiry matching rows。非空且合法时，该 candidate 即 observation_date；构造完整 matching Artifact。
6. 仅 matching population 已证明为空时，继续检查严格更早的最近 CFFEX 开市日，重复上述步骤；后续日期仍必须由完整 Calendar facts 证明。

Calendar 休市日直接跳过，不查询该日 Options；不能用 weekday、未证明的 Calendar gaps、Options 行数或 pretrade_date 代替完整开市事实。Calendar 查询分段、批量或内部遍历方式留给 implementation，但不得跳过任何更近且尚未证明不适用的 candidate。

选择成功时必须满足：

```text
observation_date <= ideal_calendar_date <= expiry_date
actual_dte >= target_dte >= 1
```

Study 不计算 observation_date 或把计算后的日期作为第四个业务输入。

## Proven absence、cache missing 与 failure

```text
DataLake cache missing != market facts proven absent
```

Product-day 被证明 complete，但 requested expiry 的 matching population 为空，才是可回溯的 proven absence。包含 DataLake 已证明完整且 universe 为空的零 Records product-day；它不是成功的 Observation Artifact。完整性与合法空 universe 的 owner 是 [Options contract universe](../../../data-lake/datasets/tushare_equity_index_options/CONTRACT_UNIVERSE.md)。

Cache 缺失必须先通过 public ensure 尝试取得事实，不能直接回退。Ensure incomplete、UnitFailure、provider operation failure、credential failure、Calendar prerequisite failure、persistence / integrity failure、非法 semantic view，或其他不能证明 completeness 的情况，均使本次 Observation invocation 明确失败。Upstream failure 不能解释为 no market data，也不能触发继续向前 fallback。完整日历下尚未发布行情的开市日同样属于失败，不是 absence。

Rows 的合法性由 [Options public contract](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md) 与 [Source facts](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md) 拥有。不得丢弃非法 rows 后宣告完整、补值或缩小 population。合法 nullable facts 不导致回溯或排除 contract。

## 回溯终止与确定性边界

不添加人为历史下界、最大回溯次数或额外 business input。每个 complete-but-absent candidate 都继续向前；找到非空完整 matching population 时成功。Calendar / Options 无法提供完整证明时立即失败；没有可表示的更早日期或日期计算无法继续时明确失败。不把未找到 expiry 发布为 empty / partial Artifact，不宣称已证明该 expiry 在所有历史日期不存在。

不使用缓存可用程度选择日期，不因 transient failure 跳过更近 candidate。日期规则在同一有效 definition 与对应合法 retained upstream facts 下确定；DataLake completeness 不保证 freshness，upstream correction 与 definition evolution 的处理仍由 [framework deferred decisions](../ARCHITECTURE.md#explicitly-deferred-decisions) 保持未决。
