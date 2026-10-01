# MO Option Risk Premium Baseline — Results

本文件是当前 Study 的 Results canonical owner。Observation Artifact 的逐 cell 含义及 Evidence Products 的 Analysis 证据含义均来自 [Method](METHOD.md)；研究问题与解释限制见 [Study entry](ARCHITECTURE.md)。

## Results

预期保留 1 个 Observation Artifact 与 2 个 Evidence Products；真实运行记录见本文件的 Real execution records；具体统计与 finding 以各 run 的 retained report 为准。成功 run 应与规范化请求、实际上游 product／query identity、返回结果 provenance、计数及排除原因共置，供人工复核。完整上游事实指纹属于 provenance，须能区分相同请求在上游事实变化前后的运行；Observation Artifact identity 只覆盖 [Method](METHOD.md) 定义的相关查询和逐 cell 语义，未影响 panel 的上游变化不改变它。运行时间或输出路径不能替代两者。

`option_outcome_panel` 是 independently retained Observation Artifact，由 `ExpiryDteOptionOutcome` 定义逐 cell 语义，供两个 Analyses 消费及逐 cell audit。它以 machine-readable 形式保留有效 observation 的日期、合约、high／low proxy、terminal close、payoff、compensation、target／actual／error；对每个无效预期 cell 保留 cell key、exclusion reasons（包括 `no_atm_or_otm_contract`），以及已选到候选时可取得的日期／合约 identity 与 target／actual／error，供复核 selection、tolerance 和排除。它不是 Analysis-defined Evidence Product；其 semantic identity 见 [Method](METHOD.md)。

| Evidence Product | `defined_by` | 必须保留的内容 |
| --- | --- | --- |
| `compensation_summary` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Machine-readable 完整 group grid、group identity、sample／unique expiry counts、预期 expiry 数、coverage、excluded-cell 数与 reason counts，以及 [Method](METHOD.md) 定义的 central／distribution statistics。两个 Analysis 的分组键与统计口径相同，共享统计值只存一次，标明两种呈现视角，不复制为两组独立证据。 |
| `risk_premium_report` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Human-readable retained report，直观显示 DTE profile、DTE × moneyness surface、CALL／PUT 及尾部分布；静态图可采用 line／point、matrix／heatmap 和适当分布图。报告必须标注 proxy、coverage、各 exclusion reason counts 与解释限制，并可追溯 summary 与 panel。 |

每个 target DTE × CALL／PUT × moneyness target 分组均在 summary／report 中出现；没有有效 observation 时以零 sample／coverage 和空统计值、空 frequency 表示，不能制造均值、分位数或图上数值。Reason counts 包括 `dte_out_of_tolerance`、`no_atm_or_otm_contract`、`moneyness_out_of_tolerance` 及其他 [Method](METHOD.md) 定义的排除原因；各 reason 可重叠，不能相加代替 excluded-cell 数。若到期日范围无真实 expiry，或整次请求没有任何有效 observation，则为 Study/sample failure，不发布成功的 panel、summary 或 report。具体文件名、序列化格式、绘图库与颜色不是当前研究语义。

## Acquisition provenance and operational progress

Successful request provenance additionally retains public Snapshot session
acquisition identity/version, basic and daily fact digests, reused/refetched
dates and execution metrics. These operational details are not incorporated
into the Observation semantic identity. CLI progress shows completed/total
dates, elapsed seconds and Source attempts. Failure identifies the date and
safe endpoint/category; a checkpoint is not successful Study evidence.

## Real execution records

2026-10-01 已完成短窗口真实验证：expiry 范围 2024-09-20 至
2024-09-20，DTE target 10，moneyness target 0。Discovery 实际为
10 个交易日，采集约 4.9 秒，共 33 次 Source attempts（包括初始
Index Daily History）。生成 request、panel、summary 与 Markdown report。
Runtime artifact 在本地配置 output root 下，不提交数据或凭证。
固定 10 日期采集基准的旧路径、高/低去重与 basic 复用路径、bulk 四 worker
路径的 high/low 公开结果一致；耗时分别约 37.1、9.0、4.8 秒，请求
分别为 160、62、32 次。性能数值属于该次环境的执行测量，不是研究 finding。

完整范围（2024-01-01 至 2026-01-01，默认 target sets）也于
2026-10-01 真实运行成功：530 个 discovery 交易日，24 个 expiry，
1,440 个预期 cells，其中 1,233 个有效，60 个 summary groups。
采集约 234.3 秒，共 1,593 次 Source attempts（含初始指数历史），
没有 Source 重试。完整 panel、summary、provenance 和 report 已发布到
配置的本地 output root。以上是 evidence coverage / execution record，
不替代 retained report 中的统计或解释限制。
短窗口使用 `--resume-source --overwrite` 验证后，10 个日期全部复用，
会话 Source attempts 为零；初始指数历史仍读取一次。
