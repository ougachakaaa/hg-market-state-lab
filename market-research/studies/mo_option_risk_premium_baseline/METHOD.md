# MO Option Risk Premium Baseline — Method

本文件是当前 Study 的 Method canonical owner。请求与上游事实见 [Inputs](INPUTS.md)；retained evidence 见 [Results](RESULTS.md)。

## Method

### Observation: `ExpiryDteOptionOutcome`

**Purpose 与粒度。** 由 [Inputs](INPUTS.md) 中发现的每个真实 expiry、resolved target DTE、CALL／PUT 和 resolved moneyness target 构成一个预期 cell；每个 cell 最多形成一个代表性合约的 realized outcome row。即使没有有效 row，预期 cell 仍须有排除记录。Observation 消费这些 Study inputs、MO Chain 公开 high／low chain facts 和 Index Daily History 的 expiry-day close；所有选择、proxy、moneyness 与 compensation 均为本 Study 语义。

**Entry 选择与容差。** 在 [Inputs](INPUTS.md) 定义的 Study-local discovery 得到的、该 expiry 有上市 MO 合约且早于 expiry 的可观察交易日中，以 `abs(actual_dte - target_dte)` 最小选择 entry 日；`actual_dte = expiry_date - entry_trade_date` 的 calendar-day distance，必须大于零。等距离时取 `actual_dte` 更大的日期。选择只看上市关系和日期，不以价格是否可用筛选候选日。先选最近日期，再检查固定 validity rule `abs(dte_error) <= 5` calendar days，其中 `dte_error = actual_dte - target_dte`；若最近日期仍超限，该 expiry × target DTE × option type × moneyness target cell 以 `dte_out_of_tolerance` 排除，不检查次近日期。对通过容差的所选日期才检查其 Study 所需 public facts；所选日期的 Study-level 价格验证失败时排除，不改选日期。保留 `target_dte`、`actual_dte`、`dte_error` 及两个日期供复核。

**合约选择与容差。** 同一 entry 日及 expiry 内，CALL 与 PUT 分开处理。`entry_underlying_proxy = (entry_underlying_high + entry_underlying_low) / 2`，CALL 的 `otm_distance = (strike - entry_underlying_proxy) / entry_underlying_proxy`，PUT 的 `otm_distance = (entry_underlying_proxy - strike) / entry_underlying_proxy`。actual `otm_distance` 的正、零、负分别表示 OTM、ATM、ITM；V1 target 只允许零（ATM）或正值（OTM）。先确认 entry underlying high／low 能形成有效 proxy，再从该 type 的 listed contracts 中以正且有限的 strike 计算 moneyness 并建立候选集；候选资格和排序不取决于 option high／low 是否可用。每个 type × target 选择 `abs(otm_distance - moneyness_target)` 最小的合约；严格等距离时先取更 OTM（较大的 `otm_distance`），再按 `instrument_id` 字典序取最小者。先选最近合约，再检查固定 validity rule `abs(moneyness_error) <= 0.025`，其中 `actual_moneyness = otm_distance`、`moneyness_error = actual_moneyness - moneyness_target`；若最近合约仍超限，该 cell 以 `moneyness_out_of_tolerance` 排除。通过容差后才验证所选合约的 option high／low；价格缺失或无效时排除该 cell，不改选次近 strike。保留 `moneyness_target`、`actual_moneyness`、`moneyness_error`、strike 和 identity。同一合约可以被多个 target 选中；这些不是独立风险事件。

**Price、payoff 与 compensation。** `entry_premium_proxy = (entry_option_high + entry_option_low) / 2`；`expiry_underlying_proxy` 是 CSI1000 在 expiry 当日的 close。CALL 的 `expiry_payoff_proxy = max(expiry_underlying_proxy - strike, 0)`；PUT 为 `max(strike - expiry_underlying_proxy, 0)`。计算：

```text
seller_compensation_points = entry_premium_proxy - expiry_payoff_proxy
seller_compensation_ratio = seller_compensation_points / entry_underlying_proxy
annualized_compensation_ratio = seller_compensation_ratio * 365 / actual_dte
```

一行须保留上述原始和派生量，并保留 entry option high／low、entry underlying high／low、expiry close、option type、所有 selection identity 和 error。若 [Inputs](INPUTS.md) 所述可选 volume 公共事实可用，额外保留所选合约的 `entry_volume`。

**Validity 与 exclusion。** 有效 row 要求一致的 expiry／entry／contract 关系、同一合约的 high 与 low、`abs(dte_error) <= 5`、`abs(moneyness_error) <= 0.025`、有限且 `0 <= low <= high` 的 option prices、有限且 `0 < low <= high` 的 underlying prices、正的 strike、正的 `actual_dte`，以及 expiry 当日有限且正的 underlying close。对合法上游结果中未通过 Study 有效性规则的预期 cell，记录可区分的原因：无可选 entry 日、`dte_out_of_tolerance`、缺该 type 或正 strike 合约、entry underlying proxy 不符合 Study 有效性、`moneyness_out_of_tolerance`、所选 option high／low 缺失或无效、expiry 当日 close 缺失，以及所选合约与 expiry 关系无效；不制造值或使用 fallback。一个 cell 可以有多个可独立诊断的原因，但 excluded-cell 总数按唯一 cell 计，reason counts 不能相加充当排除样本数。

Index Daily History 或任一单日 high／low MO Chain 的公开请求失败（包括 public chain 不允许缺失的 underlying selected price）、上游结果违反其公开契约，或同一日期的 high／low chain 在日期、expiry universe、CALL／PUT 归属、合约 identity／strike 等全局结构上矛盾时，整次 Study 失败；不将这类失败伪装成 cell exclusion 或未发现 expiry。合法的 selected option price `null` 不属于结构矛盾，按所选 cell 的价格排除处理。

**Observation Artifact identity。** `option_outcome_panel` 独立保留该 Observation；其语义 identity 包含 `ExpiryDteOptionOutcome`、规范化的四个 Study inputs，以及所消费的 Snapshot product／query identities 与实际返回的公共事实内容 identity。若上游未提供稳定的结果 identity，Study 以所消费事实的确定性内容指纹区分同一查询下的数据变化；文件名、格式、运行时间或临时路径不参与语义 identity。

### Analyses

两个 Analysis 均明确消费 `ExpiryDteOptionOutcome`，只汇总有效 rows。每个 group cell 中一个 expiry 最多贡献一行；跨 expiry 等权，不按 strike 数、volume 或同 expiry 其他 DTE 加权。`sample_count` 是有效 row 数，`unique_expiry_count` 是不同 expiry 数；二者均须输出。同一 expiry 的不同 DTE、type、target 共享 terminal market event，不能跨 cell 相加解释为独立事件数。

两者共用以下 Study-local 统计定义：对 entry premium、expiry payoff、seller compensation points／ratio／annualized ratio 各报 mean 与 median；对三种 compensation 各报最小值和 P05、P25、P50、P75、P95。经验分位数对排序样本按位置 `(n-1)*p` 作相邻值线性插值，故 P50 等于 median。正／负／零 compensation frequency 分别以 `seller_compensation_points > 0`、`< 0`、`= 0` 的个数除以有效 `sample_count`。每个 group cell 的预期 expiry 数是所发现的真实 expiry 总数；有效 unique expiry coverage 同时报 count 与其占预期 expiry 数的比例，并给出 excluded-cell 数及 reason counts。零有效样本的统计值与 frequency 明确为空，不填零。无显著性检验。

| Analysis | Purpose、consumes 与 grouping | Produces |
| --- | --- | --- |
| `DteCompensationProfile` | 回答 entry DTE 的 compensation profile；消费 `ExpiryDteOptionOutcome`；按 `target_dte × option_type × moneyness_target` 分组，以 DTE 为主要呈现轴。 | 各 DTE 的等权跨 expiry 统计、分布与覆盖。 |
| `MoneynessCompensationProfile` | 回答同一 DTE 下 moneyness 差异及 CALL／PUT 对照；消费 `ExpiryDteOptionOutcome`；按 `option_type × target_dte × moneyness_target` 分组，以 moneyness 为主要呈现轴。 | DTE × moneyness compensation surface 与分布、覆盖。 |

两个 Analysis 的分组键相同，统计约定相同，但问题视角不同；可以由同一组已计算数值呈现，无须重复计算或把其视为两组独立证据。若独立物化 Analysis Artifact，其 semantic identity 分别由 Analysis stable name、所消费的完整 `ExpiryDteOptionOutcome` Artifact identity 和本节固定统计定义决定；不能仅用 Analysis 名称或文件路径标识。
