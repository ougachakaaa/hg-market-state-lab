# Price-to-Lagged-MA Distribution retained study authority

本文档是 `Price-to-Lagged-MA Distribution`（Study 01）的唯一 canonical retained Study authority。Research 边界与 retained Study 约定见 [market-research architecture](../../ARCHITECTURE.md)；run placement 与 Study-local CLI 职责见 [Research UI authority](../../ui/ARCHITECTURE.md)；quantile、fixed-width bins 与 summary 的算法见 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)；输入产品与 public boundary 分别见 [Index Daily History product](../../../market-snapshot/src/market_snapshot/products/index_daily_history/ARCHITECTURE.md) 和 [read/application contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md)。

Stable public Study ID 是 `price-to-lagged-ma-distribution`；未来对应的 executable package 是 `market-research/src/market_research/studies/price_to_lagged_ma_distribution/`。本 Study 拥有下述研究语义与 retained evidence，不拥有 Snapshot Source facts 或 shared distribution 算法。

## Question

> 对指定指数，在给定历史 sample interval 和 lagged moving-reference definition 下，每日收盘价相对前一时点 reference 的偏离幅度如何经验分布？

Canonical daily quantity 为 `D_T = Close_T / Reference_{T-1} - 1`。本 Study 只描述所选历史样本中的分布，不从偏离推断未来涨跌、均值回归、真正市场中心或交易行为。

## Inputs

每次 Study-local semantic request 必须显式给出：

```text
instrument                       index_daily 支持的一个 index ts_code
reference_window                 正整数 N；prior actual observation count
reference_method                 sma | volume_weighted
reference_method_parameters      V1 固定为 {}，无 method-specific parameters
sample_start_trade_date          YYYY-MM-DD，含端点
sample_end_trade_date            YYYY-MM-DD，含端点
distribution_granularity         finite 且 > 0 的 decimal ratio
percentile_probabilities         非空、finite、互异且各自在 [0, 1] 的 decimal ratios
```

日期必须有效，且 start 不晚于 end。`instrument` 不固定为 CSI1000，例如可以是受产品支持的 `000852.SH`；V1 不定义股票、ETF、期货或 generic instrument routing。`market-research/research.toml` 仅拥有 `output.root`，不保存上述 Study 参数。

### Canonical Study CLI

V1 唯一 human-facing invocation 使用 repository CLI 的透明转发与本 Study 的 study-local parser：

```bash
poetry run python dev.py research run \
    price-to-lagged-ma-distribution \
    --instrument 000852.SH \
    --window 60 \
    --method sma \
    --start 2015-01-01 \
    --end 2026-09-01 \
    --granularity 0.005 \
    --percentiles 0.01,0.05,0.10,0.20,0.50,0.80,0.90,0.95,0.99
```

这七个 study-specific flags 均为 required，没有 hidden default；可另加 `--overwrite`，默认 false，只表示允许替换已存在的完整 run directory，placement 与 collision 语义遵循 Research UI authority。`--instrument` 是 index `ts_code`；`--window` 是正整数、此前实际 observation 条数；`--method` 只接受 `sma` 或 `volume_weighted`；`--start` 与 `--end` 是有效的 `YYYY-MM-DD`、含端点 calendar bounds，且 start 不晚于 end；`--granularity` 是 finite 且大于零的 decimal ratio；`--percentiles` 是一个逗号分隔的非空 decimal-probability 参数，每项 finite、在 `[0, 1]` 内且按数值不得重复。

`--granularity 0.005` 表示 0.5%；`--percentiles 0.01,0.05,0.95,0.99` 表示 P1、P5、P95、P99。V1 CLI 不接受百分号输入，也不提供 `--method-param`、`--decay`、`--half-life`、`--lambda` 等 method-specific flags。百分号只可用于 human-facing report / visualization；CLI 与 machine-readable result 使用 decimal ratios。

CLI 仅是 inbound representation；study-local parser 将 `--instrument`、`--window`、`--method`、`--start`、`--end`、`--granularity`、`--percentiles` 依次映射为上述 semantic request 的 `instrument`、`reference_window`、`reference_method`、`sample_start_trade_date`、`sample_end_trade_date`、`distribution_granularity`、`percentile_probabilities`，并设置 `reference_method_parameters = {}`。Percentiles 必须解析、校验、对重复数值报错而非静默去重，再按数值升序规范化；等价 numeric spelling 得到相同 semantic request 与 run identity，不使用 raw argv 生成 run key。

Study-local composition 通过 Index Daily History 的 production-ready public Python entry 提交：

```text
IndexDailyHistoryRequest(
    ts_code = instrument,
    start_trade_date = sample_start_trade_date,
    end_trade_date = sample_end_trade_date,
    pre_start_observation_count = reference_window,
)
```

Study 消费完整 `IndexDailyHistoryResult` 中分开的 `warmup_observations[]` 与 `sample_observations[]`，不自行访问 `index_daily` Source、credential、Raw、product-private Preparation、persistence layout 或 HTTP DTO。请求区间是 calendar bounds；真正进入样本的是产品返回的实际日线 observations。Study 不制造周末、休市日，不查找最近交易日，也不重新定义 Snapshot 的 observation completeness。

## Method

### Lagged reference 与 warm-up

对每个 sample observation `T`，`reference_window = N` 指该指数在 `T` **之前紧邻的 N 条实际 observations**，不是 N 个日历日。按 `trade_date` 升序连接 warm-up 和 sample observations，计算：

```text
Reference_{T-1} = reference_method(observations T-N ... T-1)
D_T             = Close_T / Reference_{T-1} - 1
```

`Close_T` 绝不参与自己的 `Reference_{T-1}`。第一条 sample observation `T0` 使用恰好 N 条 pre-start warm-up observations 形成 reference，并进入 deviation sample；后续 sample rows 可以成为更晚日期的 lagged reference 输入。Warm-up rows 只用于 reference，不进入最终统计样本。产品不能提供完整 warm-up 时整个请求失败，Study 不缩短窗口或丢弃样本起点。

### V1 reference methods

`sma` 对 prior N 条 `close` 取算术平均。`volume_weighted` 对同一 prior N 条计算：

```text
Reference = sum(close_i * volume_i) / sum(volume_i)
```

SMA 所需的每个 `close` 必须可用；其正值与 finite 约束由 Snapshot product contract 保证，Study 遇到违反 contract 的结果仍须显式失败。Volume-weighted method 要求每个所需 `volume` 非 null、finite 且 `>= 0`，并要求 `sum(volume_i) > 0`；否则整个 run 失败，不填值、不回退 SMA、不删除日期。任一 method 的最终 reference 必须 finite 且严格大于零，计算出的 deviation 也必须 finite；失败不得变成 NaN、infinity、除零或静默跳过。

V1 只正式定义 `sma` 与 `volume_weighted`，两者的 `reference_method_parameters = {}`。`decay_weighted` 明确 deferred：当前尚未锁定 weight function、decay parameter semantic、normalization rule 与 age direction，Implementation Agent 不得自行发明 decay formula。未来新增 decay 或其他加权方法，须先在本 Study authority 中定义 canonical method token、method-specific parameters、deterministic weighting formula 与 validation/failure semantics；不能以含糊的 `weighted`、`decay` 或 `custom` 名称代替公式。当前 reference 与 deviation 仅由本 Study 拥有，不提升为 shared MA、reference 或 feature framework。

### Daily observations 与 eligible sample

每条 Snapshot `sample_observations[]` 对应且只对应一条 `PriceToLaggedMAObservation`：

```text
trade_date
instrument
close
reference_ma                 Reference_{T-1}
deviation                    close / reference_ma - 1
```

`deviation`、granularity、bins 和 percentile values 均使用 decimal ratio unit：`0.05` 表示 `+5%`，不在 canonical numeric result 中写成 `5`。成功 run 的 `deviations[]` 与 Snapshot sample observations 一一对应，`deviation_count = sample_observation_count`。V1 不做 outlier removal、winsorization、clipping、regime filtering 或 null-reference row dropping；任一 sample day 无法计算即整个 run 失败。

### Empirical distribution

Study 将完整 `deviations[]` 交给 shared distribution capability。`percentile_probabilities` 在验证互异后按数值升序成为 canonical request 与输出顺序；quantile interpolation 采用共享 convention。`distribution_granularity` 与 deviation 使用同一 decimal-ratio unit；zero-anchored、左闭右开、连续 fixed-width bins 及其 count/frequency 采用共享 authority，不在 Study 中重定义 bucket 算法。

Retained summary 使用共享的 `sample_count`、`mean`、`median`、`sample_standard_deviation`、`min`、`max`。任意非空且有效的 deviation sample 均可成功；`sample_count = 1` 时，daily observation、fixed-width distribution、empirical percentiles、mean、median、min 与 max 仍有定义，`sample_standard_deviation = null`，不使整个 Study 失败，也不伪造 `0`、NaN 或 infinity。`sample_count >= 2` 时使用 `ddof = 1` 的 sample standard deviation。Study 不添加 skewness、kurtosis、normality test、KDE 或 parametric fit。

## Execution identity

一次 retained run 只表示一个完整 semantic request，不自动 sweep 多个 window 或 method。重复运行不同参数可构成后续人工比较，但本 Study 不定义 Experiment Engine。

Study-owned run key 包含 Inputs 列出的全部字段。先验证 request，再将日期规范为 `YYYY-MM-DD`，method 使用上述 canonical token，method parameters 规范为 V1 的空对象，将所有 finite decimal-ratio 数值规范为无指数、无无意义尾零的十进制字符串（负零规范为 `0`），并将 percentile probabilities 按数值升序排列。不从 CLI 原始 argv 派生 identity。

`instrument` 使用 Study request 校验后的 `ts_code` 原值；Snapshot product 仍拥有是否支持该 identity 的最终判定。上述规范化在调用 Snapshot 前完成，以遵守 Research UI 的 collision-before-Snapshot 规则。对包含全部字段、字段名按字典序排列的规范对象，生成 UTF-8、无多余空白的 JSON；run key 为其 SHA-256 digest 的完整小写十六进制字符串。等价的 CLI 数值拼写或 percentile 输入顺序得到相同 key；任何 evidence-affecting semantic parameter 都参与 key。当前时间、随机值、输出路径和执行顺序不参与 identity。Study-local CLI 将该 key 作为不透明目录名交给 Research UI，placement 与 collision/overwrite 行为遵循其 authority。

## Results 与 retained evidence

成功 run 在 canonical run directory 中至少保留：

| Artifact | Study-owned content |
| --- | --- |
| `request.json` | public Study ID、Study-owned run key、完整规范 semantic request、Snapshot result 中实际请求 bounds 与 warm-up/sample counts |
| `observations.csv` | 每个 sample day 的 `trade_date,instrument,close,reference_ma,deviation`；按日期升序，`deviation` 使用 decimal ratio，`close` 与 `reference_ma` 保持价格单位 |
| `distribution.csv` | 每个连续 fixed-width bin 的 numeric `lower_bound,upper_bound,count,frequency`，包括 zero-count bins |
| `percentiles.csv` | 按 probability 升序排列的 numeric `probability,value` |
| `summary.json` | `sample_count,mean,median,sample_standard_deviation,min,max`；仅当 `sample_count < 2` 时 `sample_standard_deviation` 为 JSON `null` |
| `report.md` | Question、Inputs、reference definition、sample、distribution result 与 Limitations 的简洁人类可读说明 |
| `distribution.png` | 每个成功 run 必须保留的 Python-generated static empirical-distribution 图 |

机器可读结果的数值保留上述 canonical unit；百分号仅属于报告或图形标注。图形帮助观察分布，不增加 signal zone、forecast 或 trading recommendation。本 Study 尚未运行真实研究，因此当前没有统计数值、plot 或 finding；首次真实 run 才产生上述 evidence。

## Limitations 与后续研究

结果只描述指定指数、日期边界、reference definition 与完整历史 sample 下的经验分布；更换任一项会改变研究问题。偏离零较远不自动意味着 mispricing、overbought/oversold 或均值回归机会。Volume-weighted reference 使用 Snapshot 提供的成交量事实，其权重不表示可交易性或未来价格影响。

Future return、forward path、mean-reversion testing、best/optimal MA、true market center、center migration、regime detection、basis、volatility/valuation conditioning、signal generation、position sizing、portfolio decision、forecasting、modeling 与 backtesting 均不属于本 Study。未来 Study 若真正复用 lagged reference/deviation semantic，须先作新的 semantic decision，才考虑将其提升为 shared Research semantic；本 Study 不预建该抽象。
