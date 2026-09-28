# Price-to-Lagged-MA Short-Horizon Reversion retained Study authority

本文档是本 retained Study 的独立 canonical authority。Stable public Study ID 为 `price-to-lagged-ma-short-horizon-reversion`，对应的 runnable package 名为 `price_to_lagged_ma_short_horizon_reversion`。Authoring 遵循 [Study Authority Authoring](../AUTHORING.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，Study-local CLI、配置、run placement 与 collision/overwrite 规则见 [Research UI authority](../../ui/ARCHITECTURE.md)。Lagged reference 与 deviation 引用 [Price-to-Lagged-Reference Research Semantics](../../shared/price_to_lagged_reference/ARCHITECTURE.md)，empirical quantile 引用 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)；输入事实只来自 [Index Daily History product](../../../market-snapshot/src/market_snapshot/products/index_daily_history/ARCHITECTURE.md) 的 [public read/application contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md)。

## Question

对指定指数，当日收盘价相对 lagged moving reference 的偏离程度，与未来短周期反向价格运动的发生概率和运动幅度之间是什么关系？对每个 deviation bucket × horizon 分别回答：未来价格向相反方向运动的概率是多少；若确实发生，典型反向运动幅度是多少。本 Study 检验短暂的条件性历史关系，不寻找新趋势或长期反转。

核心待检验假设专指默认的 60-observation SMA reference：price-to-lagged-60MA deviation percentile 越接近分布两端，未来 1–5 条交易观察内的反向运动概率和发生反向运动后的典型幅度可能越大。其他受支持的 reference method/window 与其他 forward horizons 是同一研究方法下的探索性配置；它们不自动继承“60MA / 1–5D”这一特定假设，也不把假设写成 finding。

预期 evidence 应能比较尾部与中部、效应是否单调或只集中于极端桶、上尾与下尾、各配置 horizon，以及 5D 窗口内的暂时反弹与 5D 期末回报。与只回答当前偏离历史位置的 Distribution Study 平行保留，本 Study 回答从该状态出发随后发生了什么。

## Inputs

一次 semantic request 包含以下 Study-owned 输入。日期为含端点的 calendar bounds，实际 sample 只由 Index Daily History 返回的交易 observations 构成。

| Semantic input | 用户可见 CLI | 必填与默认 | 校验及含义 |
| --- | --- | --- | --- |
| `instrument` | `--instrument <ts_code>` | 必填，无默认 | 非空、无首尾空白的单个指数 identity；是否受 Index Daily History 支持由该产品判定，不改写大小写或使用别名。 |
| `sample_start_trade_date` | `--start YYYY-MM-DD` | 必填，无默认 | 有效日期，且不晚于 end。 |
| `sample_end_trade_date` | `--end YYYY-MM-DD` | 必填，无默认 | 有效日期，且不早于 start。 |
| `reference_method` | `--method sma` 或 `--method volume_weighted` | 可选，默认 `sma` | 只接受 shared lagged-reference authority 当前正式定义的两个 method token；其计算和失败语义由该 shared authority 拥有。 |
| `reference_window` | `--window <N>` | 可选，默认 `60` | 正整数，表示每个 sample date 之前紧邻的实际 observation 条数。 |
| `percentile_bucket_edges` | `--bucket-edges <p0,p1,...,pk>` | 可选，默认 `0,0.05,0.10,0.20,0.80,0.90,0.95,1` | 至少两个 finite decimal ratios；首项为 0、末项为 1，其余严格递增且均在 `[0,1]`。相邻两项构成一个 bucket；CLI 不接受百分号。 |
| `forward_horizons` | `--horizons <h1,h2,...>` | 可选，默认 `1,3,5` | 非空、互异的正整数集合，以后续实际交易 observations 计数；重复值报错，输入顺序不改变语义。 |

例如：

```bash
lab research run price-to-lagged-ma-short-horizon-reversion \
    --instrument 000852.SH --start 2015-01-01 --end 2026-09-01 \
    --method sma --window 60 \
    --bucket-edges 0,0.05,0.10,0.20,0.80,0.90,0.95,1 \
    --horizons 1,3,5
```

上述可选 flags 省略时使用相同 semantic defaults。Study-local CLI 另提供 `--overwrite`，默认 false；它只允许按 Research UI authority 替换已存在的完整 run directory，不改变研究请求或 run identity。Study 参数不写入共享 `research.toml`；输出根目录由 Research UI 配置提供。

Study-local CLI 通过 Index Daily History 的 production-ready public Python entry 提交 `ts_code = instrument`、上述起止日期，以及 `pre_start_observation_count = reference_window`。消费分开的 `warmup_observations[]` 与 `sample_observations[]`：warm-up 只形成 lagged reference，不进入 percentile population 或 forward outcome。产品提供精确 warm-up、有效 close 和有序 sample 的成功/失败契约；本 Study 不读取 Source、Capture、Raw、私有 Preparation、credential 或 HTTP DTO，不填补不存在的交易日，也不为 sample end 之后的 forward outcome 补取数据。

## Method

### 状态、经验 percentile 与归桶

对每个 sample observation `T`，使用 shared lagged-reference authority 定义的 `D_T = Close_T / Reference_{T-1} - 1`。此前 `reference_window` 条实际 observations、`Close_T` 不进入自身 reference、`sma`、`volume_weighted`、当前无 method-specific parameters、warm-up 完整性及计算失败规则均以该 shared authority 为准；不能因某日不可计算而缩小样本或静默删行。

将**完整 sample** 的所有有效 `D_T` 作为 empirical quantile 的 numeric sample，按 shared convention 求每个配置 percentile edge 的 deviation 阈值。`D_T = 0` 和后来因 forward 数据不足而不能进入方向性统计的日期仍参与阈值计算。各 bucket 按相邻阈值形成左闭右开区间；共同阈值上的观察归较高 bucket，最后一个 bucket 包含最大值。相同 `D_T` 总归同一 bucket；阈值重合可使 bucket 为空，不按日期或排序位置拆分相同状态。

### Forward outcome 与有效观察

对正整数 horizon `h`，`R_{T,h} = Close_{T+h} / Close_T - 1`，其中 `T+h` 是 sample 内第 `h` 条后续实际交易 observation，不是日历日。`D_T < 0` 时 `MR_{T,h} = R_{T,h}`；`D_T > 0` 时 `MR_{T,h} = -R_{T,h}`。`MR > 0` 表示未来价格朝当日 reference 的方向移动，`MR < 0` 表示继续远离；只衡量未来价格回报方向，不把未来 deviation 缩小当作主要 outcome。`D_T = 0` 无反向方向，从所有 MR/MFE 统计排除。

除配置的 horizons 外，固定计算 5D MR，保证所有配置均能与 5D MFE 比较；若配置已含 5，只计算和保留同一个 5D MR 结果。5D mean-reversion MFE 为 `max(0, MR_{T,1}, MR_{T,2}, MR_{T,3}, MR_{T,4}, MR_{T,5})`，表示从 `Close_T` 出发、`T+1` 至 `T+5` 内达到的最强有利方向价格移动；全程无有利移动时为零。MFE 与 5D MR 使用完全相同的有效日期，并属于固定 horizon MR 的次要补充。

每个 bucket 与 evaluation horizon（配置的 horizons 加固定 5）的有效观察必须同时满足 `D_T != 0`、归属该 bucket、sample 内有完整的第 `h` 条后续 observation。各 horizon 独立筛选，绝不跨越 sample end；更长 horizon 可以有更少有效观察。反向运动定义为严格 `MR_{T,h} > 0`；`MR = 0` 留在有效样本中，但不计为 reversal。主结果拆为 `reversal_probability = reversal_count / eligible_sample_count`，以及只对 reversal observations 计算的 conditional reversal magnitude mean 与 median（median 是主要典型幅度）。无 reversal 时条件样本数为零，条件 mean/median 未定义；无有效 MR 时概率也未定义。全部有效 MR 的 mean 与 median 作为合并反向和非反向结果的辅助 evidence 保留；mean 为算术平均，median 用 shared empirical quantile `p=0.5`。5D MFE mean 与 median 基于相同的 5D 有效观察，仍为 path-level 辅助 evidence。若全体 bucket 合计没有一条有效的 5D MR/MFE 观察，run 失败，不发布完整结果。

### Retained run identity

Run identity 包含 `instrument`、两端 sample dates、`reference_method`、`reference_window`、`percentile_bucket_edges` 和 `forward_horizons` 的**有效 semantic values**，包括省略 flag 后采用的默认值；由 shared lagged-reference authority 定义且目前固定为空对象的 `reference_method_parameters = {}` 也记录在规范请求中。先验证请求，再把日期规范为 `YYYY-MM-DD`、method 规范为 canonical token、window 和 horizons 规范为十进制整数；finite decimal edges 规范为无指数、无无意义尾零的十进制字符串（负零为 `0`），并保持严格递增的 edge 顺序。Horizon 集合按数值升序规范化；不同输入顺序得到相同请求和 key。`instrument` 使用经输入校验的 `ts_code` identity，不发明指数别名或大小写折叠。

规范对象用上述 semantic 字段名作为 JSON keys：instrument、method 与日期为字符串，window 与 horizon 数组成员为 JSON 整数，edge 数组成员为规范十进制字符串，method parameters 为空对象。以 keys 按字典序排列、无多余空白的 UTF-8 JSON 计算 SHA-256；完整小写十六进制 digest 就是 Study-owned run key。语义相同的默认/显式输入、等价 decimal 拼写或 horizon 顺序产生相同 key；任何这些 semantic values 的变化必须改变 identity。原始 argv、`--overwrite`、output root、执行时间、随机值和运行顺序均不参与。Study-local CLI 在调用 Snapshot 前完成 key 和 Research UI 的 collision 检查，并将 key 作为不透明目录名交给 Research UI；已有 run 的替换语义由后者拥有。

## Results

每个成功 run 必须保留可复核的 machine-readable evidence。最低语义结构如下；具体文件名与编码格式不是本 Study 的稳定语义契约：

| 内容 | 必须保留的字段与解释 |
| --- | --- |
| Request / provenance | public Study ID、规范 semantic request、run key、Index Daily History 产品来源与提交的 public request、产品返回的实际请求 bounds、warm-up/sample counts、sample 首末实际 trade date。 |
| Bucket metadata | 每个配置 bucket 的顺序、percentile 下/上 edge、对应 deviation 下/上阈值、`bucket_observation_count`；percentile 与 deviation 均为 decimal ratios。 |
| MR / reversal statistics | 每个 bucket × evaluation horizon 一条记录，含 horizon、是否属于配置 horizons、`eligible_sample_count`、`reversal_count`、`reversal_probability`、`conditional_reversal_magnitude_sample_count`、`conditional_reversal_magnitude_mean`、`conditional_reversal_magnitude_median`、`unconditional_mr_mean`、`unconditional_mr_median`。运动幅度与 MR 使用 decimal ratio，概率使用 `[0,1]` ratio。 |
| Fixed 5D MFE | 每个 bucket 一条记录，含与同 bucket 5D MR 相同的 `sample_count`、MFE mean 与 median；MFE 使用 decimal ratio。 |
| Exclusions | 每个 bucket × evaluation horizon 报告零偏离排除数与缺少该 horizon forward observation 的排除数；5D MFE 复用 5D MR 的排除和有效样本数。 |

`bucket_observation_count` 包含归入该 bucket 的所有 sample 日期，即使该日期为零偏离或缺少 forward 数据。排除原因互斥：先将零偏离计入 `zero_deviation_excluded_count`；仅对剩余非零偏离日期计 `insufficient_forward_excluded_count`。因此对每个 bucket × horizon，`bucket_observation_count = zero_deviation_excluded_count + insufficient_forward_excluded_count + eligible_sample_count`。`conditional_reversal_magnitude_sample_count = reversal_count`；有效样本非零时 `reversal_probability = reversal_count / eligible_sample_count`。没有 reversal 时 count 为零、条件 mean/median 为 `null`。配置中的每个 bucket 和 evaluation horizon 即使没有有效观察也必须保留记录：有效数与 reversal 数均为零，概率及所有 MR/条件幅度统计为 `null`，不得伪造零收益或省略该组。保留实际 bucket 阈值、上述计数和产品来源以复核不同 horizon 的分母。

人类可读 evidence 必须包括每 bucket 一行的主表、辅助统计表、简洁研究报告和 Python 生成的两张独立静态主图。主表先列实际 deviation range、percentile range 和 bucket count，再对每个**配置的** horizon 列 reversal probability 与 conditional reversal magnitude median。辅助表列各 horizon 的有效数、reversal/条件幅度样本数、条件 mean、全部样本 MR mean/median、互斥排除数，以及固定 5D MR 与 5D MFE 的 count/mean/median；配置已含 5 时只使用同一份 5D MR，空组明确标为空。

### Visualization

两张主图使用完全相同、按负偏离到正偏离排列的**实际 deviation range** 作为主要横轴标签，percentile range 只作为表中的次要 metadata。一张展示 reversal probability，并绘制 50% 参考线；另一张展示只对已发生 reversal 计算的 conditional magnitude median。两图均对照配置 horizons，对空统计留空；不得以 mean MR 单图替代这两个主视图。边界标签应按实际归桶规则表达（内部区间左闭右开，最末桶含 sample 最大值）；展示可做百分比舍入，精确阈值仍在 machine-readable evidence。报告记录 Question、规范 Inputs、两个分母、样本与排除情况、实际分桶范围、各 horizon 概率与条件幅度各自最高的区间、固定 5D MR/MFE 比较及 Limitations。机器数值保持 decimal ratios。

本地 retained run 的具体统计数值与 finding 留在其 evidence 中，不预写进本 authority；成功 run 必须按以上 contract 生成完整 evidence。

## Limitations

结果只描述所选指数、reference rule、样本区间、bucket edges 和 horizons 下的条件性历史关系。Percentile 阈值来自本次完整样本；改变样本或 reference 会改变阈值和归桶。其他 reference 配置与不在 1–5D 范围内的 horizons 是探索性对照，不能被表述为默认 60 SMA 核心假设的直接检验。

短期反向价格移动不证明长期趋势反转、价格被 moving average 因果吸引，或 moving average 构成“支撑”“阻力”。未来 deviation 缩小可能来自价格、moving reference 或两者同时移动；主要 outcome 因此采用未来指数收益。结果不证明扣除成本后的盈利能力，也不单独构成可执行交易信号、forecast、decision 或 recommendation。

## Acceptance

- Study request 的 public ID、每项 CLI 表达、必填性、默认值和校验必须与 Inputs 一致；省略/显式等价值产生相同规范请求与 run key，改变任何 semantic input 产生不同 identity。Run placement、collision 和 `--overwrite` 遵循 Research UI authority。
- 每个 sample date 的 lagged reference/deviation 符合 shared lagged-reference authority；完整 deviation sample 按 shared quantile convention 生成可配置阈值，相同值不拆桶，零偏离和 forward 不足日期仍参与阈值。默认 60 SMA、默认 buckets 与 1/3/5 horizons 对应 Question 的核心检验；其他有效配置作为探索性结果标示。
- 每个配置 horizon 与固定 5D 的 forward return 只使用 sample 内的实际交易 observations；上下尾按同一正向 MR 解释，5D MFE 捕捉窗口内最强有利移动，且与固定 5D MR 使用同一有效日期。无有效 5D 观察时失败，不发布成功 evidence。
- 每个 bucket × evaluation horizon 均有有效 MR 数、reversal 数、概率、条件幅度数/mean/median、全部 MR mean/median；条件数等于 reversal 数，概率以有效 MR 数为分母。无 reversal 与空有效组的不同 `0`/`null` 状态准确保留。5D MFE 有 count/mean/median；Bucket 总数、互斥零偏离/forward 不足排除数与有效数能够逐组对账；规范请求、实际样本与 Snapshot provenance 足以复核结果。
- 成功 run 同时提供 machine-readable evidence、以实际 deviation range 为首列的每 bucket 主表、辅助统计、报告及配置 horizon 的两张独立静态主图；两图横轴一致、概率图含 50% 参考线。报告比较固定 5D MR 与 MFE，并保持 Limitations 的非因果、非交易结论边界。任何 finding 只有实际执行并获得 evidence 后才能陈述，核心假设不得预写为已成立。
