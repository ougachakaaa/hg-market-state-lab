# MO Option Risk Premium Baseline — Results

本文件是当前 Study 的 Results canonical owner。Observation Artifact 的逐 cell 含义及 Evidence Products 的 Analysis 证据含义均来自 [Method](METHOD.md)；研究问题与解释限制见 [Study entry](ARCHITECTURE.md)。

## Results

预期保留 1 个 Observation Artifact 与 2 个 Evidence Products；目前没有真实运行、数值、图形或 finding。成功 run 应与规范化请求、实际上游 product／query identity、返回结果 provenance、计数及排除原因共置，供人工复核。结果 provenance 应足以区分相同请求在上游事实变化前后的证据；运行时间或输出路径不能替代它。

`option_outcome_panel` 是 independently retained Observation Artifact，由 `ExpiryDteOptionOutcome` 定义逐 cell 语义，供两个 Analyses 消费及逐 cell audit。它以 machine-readable 形式保留有效 observation 的日期、合约、high／low proxy、terminal close、payoff、compensation、target／actual／error；对每个无效预期 cell 保留 cell key、exclusion reasons（包括 `no_atm_or_otm_contract`），以及已选到候选时可取得的日期／合约 identity 与 target／actual／error，供复核 selection、tolerance 和排除。它不是 Analysis-defined Evidence Product；其 semantic identity 见 [Method](METHOD.md)。

| Evidence Product | `defined_by` | 必须保留的内容 |
| --- | --- | --- |
| `compensation_summary` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Machine-readable 完整 group grid、group identity、sample／unique expiry counts、预期 expiry 数、coverage、excluded-cell 数与 reason counts，以及 [Method](METHOD.md) 定义的 central／distribution statistics。两个 Analysis 的分组键与统计口径相同，共享统计值只存一次，标明两种呈现视角，不复制为两组独立证据。 |
| `risk_premium_report` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Human-readable retained report，直观显示 DTE profile、DTE × moneyness surface、CALL／PUT 及尾部分布；静态图可采用 line／point、matrix／heatmap 和适当分布图。报告必须标注 proxy、coverage、各 exclusion reason counts 与解释限制，并可追溯 summary 与 panel。 |

每个 target DTE × CALL／PUT × moneyness target 分组均在 summary／report 中出现；没有有效 observation 时以零 sample／coverage 和空统计值、空 frequency 表示，不能制造均值、分位数或图上数值。Reason counts 包括 `dte_out_of_tolerance`、`no_atm_or_otm_contract`、`moneyness_out_of_tolerance` 及其他 [Method](METHOD.md) 定义的排除原因；各 reason 可重叠，不能相加代替 excluded-cell 数。若到期日范围无真实 expiry，或整次请求没有任何有效 observation，则为 Study/sample failure，不发布成功的 panel、summary 或 report。具体文件名、序列化格式、绘图库与颜色不是当前研究语义。
