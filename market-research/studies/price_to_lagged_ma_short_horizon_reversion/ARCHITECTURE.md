# Price-to-Lagged-MA Short-Horizon Reversion retained study authority

本文档是 `Price-to-Lagged-MA Short-Horizon Reversion` 的独立 canonical retained Study authority。Stable public Study ID 为 `price-to-lagged-ma-short-horizon-reversion`。Research 边界与 Study authoring contract 分别见 [market-research architecture](../../ARCHITECTURE.md) 和 [Study Authority Authoring](../AUTHORING.md)；lagged reference / deviation 的 canonical 定义见 [Price-to-Lagged-MA Distribution](../price_to_lagged_ma_distribution/ARCHITECTURE.md)，empirical quantile convention 见 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)；输入与 public boundary 见 [Index Daily History product](../../../market-snapshot/src/market_snapshot/products/index_daily_history/ARCHITECTURE.md) 和 [read/application contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md)。本 Study 通过引用沿用已有状态语义，独立拥有下述条件性未来收益研究语义；本 authority 不启动 Study implementation 或 execution。

## Question

对指定指数，在当前价格相对前一时点 moving reference 的偏离落入给定 percentile bucket 时，随后 1、3、5 条实际交易观察内的反向价格移动有多强？核心待检验假设是：当前 price-to-lagged-60MA deviation percentile 越极端，未来 1–5 个交易日的短期反向移动越强；该假设不是预设 finding。

本 Study 与只回答当前偏离历史位置的分布 Study 平行保留，关注短期条件性历史关系。证据应允许比较分布尾部与中部、单调变化与仅极端桶集中、上尾与下尾、不同 horizon，以及窗口内短暂反弹与期末收益的差异；不研究新趋势或长期反转。

## Inputs

一次研究由以下 Study-specific 输入确定：

| 输入 | 语义 |
| --- | --- |
| `instrument` | Index Daily History 支持的一个指数 identity。 |
| `reference_method`、`reference_window` | 与分布 Study 相同的 moving-reference rule；默认 `sma`、此前 60 条实际 observations。方法语义及可用方法由分布 Study 的 canonical authority 定义。 |
| `sample_start_trade_date`、`sample_end_trade_date` | 研究样本的含端点 calendar bounds；样本是产品在区间内返回的实际交易 observations。 |
| `percentile_buckets` | 可配置的 percentile 区间边界，必须从 0% 连续覆盖到 100%；默认 `0–5%`、`5–10%`、`10–20%`、`20–80%`、`80–90%`、`90–95%`、`95–100%`。 |
| `forward_horizons` | 以未来实际交易 observations 计数；`1D / 3D / 5D` 始终必需，可额外增加其他正整数 horizon。5D rebound MFE 是本 Study MVP 的固定研究结果。 |

输入事实只经 Index Daily History 的 public application result 获取。请求 `pre_start_observation_count = reference_window`，使用分开的 warm-up 与 sample observations；warm-up 只形成 sample 首日的 lagged reference，不进入 percentile population 或 forward outcome。没有隐式交易日填补，也不将 sample 结束日之后的观察引入 forward calculation。

## Method

### 状态与分桶

对每个 sample observation `T`，沿用分布 Study 的状态定义 `D_T = Close_T / Reference_{T-1} - 1`：reference 只使用此前 `reference_window` 条实际 observations，`Close_T` 不进入自身 reference。SMA 与 volume-weighted method 的完整计算、输入有效性和失败条件以该 canonical authority 为准；本 Study 不另立 reference 或 deviation 定义。

在本次完整研究样本的所有有效 `D_T` 上，按 shared empirical quantile convention 计算所配置 percentile 边界对应的 deviation 阈值，包括后来因缺少 forward 数据或 `D_T = 0` 而不能进入方向性统计的日期。按 deviation 阈值归桶，同一 `D_T` 始终进入同一桶；共同阈值上的观察归较高桶，最后一桶包含最大值。阈值重合可以产生空桶，不按日期或排序位置拆分相同状态。零偏离日仍参与 percentile 阈值计算，但由于没有反向方向，不进入 MR / MFE 统计；结果报告其排除数量。

### Forward return 与反向移动

对 horizon `h`，`R_{T,h} = Close_{T+h} / Close_T - 1`；`T+h` 指样本内第 `h` 条后续实际交易 observation，不是日历日。方向归一化结果为：`D_T < 0` 时 `MR_{T,h} = R_{T,h}`，`D_T > 0` 时 `MR_{T,h} = -R_{T,h}`。`MR > 0` 表示价格朝 moving reference 的方向移动，`MR < 0` 表示价格继续朝相反方向移动。主要可比结果是此固定 horizon 的未来指数收益，而不是未来 deviation 的收敛程度。

5D mean-reversion MFE 为 `max(0, MR_{T,1}, MR_{T,2}, MR_{T,3}, MR_{T,4}, MR_{T,5})`，表示 `T+1` 至 `T+5` 内从 `Close_T` 出发达到的最强反向价格移动；没有有利移动时为零。它是固定 horizon MR 的次要补充，记录可能在 `T+2` 或 `T+3` 出现并随后消退的短暂反弹。

各 horizon 独立使用在研究样本结束前具备完整对应 forward observation 的日期，不跨越 sample end 补取数据。5D MFE 使用与 5D MR 相同的有效日期。每个 bucket、horizon 的 `sample_count` 是该组合的有效且非零偏离观察数；均值是算术平均，median 使用 shared empirical quantile convention，positive rate 是严格 `MR > 0` 的占比。配置中的空桶仍出现在结果中，以 `sample_count = 0` 和空统计值表示，不伪造零收益。若整个研究没有至少一条有效 5D 观察，不能产出本 Study 要求的完整结果。

## Results

每个 percentile bucket 和每个 forward horizon 至少保留 `sample_count`、MR mean、MR median 与 `MR > 0` 的比例；5D 另保留同一有效样本的 MFE mean 与 median。结果保留可识别的 bucket 边界、各 horizon 计数、零偏离排除数量及样本末端缺少 forward observations 的排除情况，使不同 horizon 的分母可复核。收益、偏离与 percentile 数值在机器可读结果中使用 decimal ratio unit。

人类可读主表以每个 bucket 一行展示 1D / 3D / 5D 的 MR 均值、positive rate、对应计数和 5D MFE；MR median 可以在同表或详细结果中展示。主图以当前 deviation percentile / bucket 为横轴、mean-reversion return 为纵轴，对照 1D、3D、5D；图形帮助辨认尾部模式，不表达因果性。保留表格、机器可读结果及研究图形，以便比较上下尾、不同 horizon 和 5D MFE 与 5D 期末 MR。

本 Study 尚未执行真实研究，因此当前没有统计数值、图形、evidence 或 finding；上述内容是预期 retained evidence 与解释规则。

## Limitations

结果只描述所选指数、reference rule、样本区间、percentile buckets 和 forward horizons 下的条件性历史关系。样本内 percentile 阈值依赖完整研究样本；更换样本会改变桶界和结果。短期反向价格移动不证明长期趋势反转、价格受到 moving average 的因果吸引，或 moving average 构成“支撑”“阻力”。

未来 deviation 缩小可能来自价格移动、moving reference 自身移动或二者共同移动；因此主要 outcome 使用未来指数收益。研究结果不证明扣除成本后的盈利能力，也不单独构成可执行交易信号、forecast、decision 或 recommendation。

## Acceptance

设计完整性要求：状态使用分布 Study 的 lagged-reference / deviation 语义；可配置 percentile buckets 的阈值来自完整研究样本；1D、3D、5D 以实际交易 observations 定义；上、下尾按同一 MR 正方向比较；5D MFE 捕捉窗口内最强反向移动，且结果保持条件性 evidence 的解释边界。

完整研究结果要求：每个配置 bucket 和 horizon 都呈现对应有效样本计数、MR mean、median 与 positive rate，5D 呈现 MFE mean / median；表格、机器可读结果和主图可供复核。零偏离日及没有足够未来数据的边界日期须显式排除并报告；空桶须保留为空统计；至少一条有效 5D 观察才能形成完整结果。任何真实结论须由实际 evidence 支持，不把核心假设写成已证实结论。
