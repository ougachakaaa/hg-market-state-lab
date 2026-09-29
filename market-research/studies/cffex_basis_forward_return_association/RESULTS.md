# CFFEX Study Results authority

本文档从属于 [Study entry](ARCHITECTURE.md)，拥有 retained evidence、provenance、machine-readable 表、human-readable report 与静态图的最低语义契约。统计定义及各 evidence 的产生关系见 [Method](METHOD.md)。

## Results

成功 retained run 同时保留 machine-readable evidence、human-readable report/table 和 Python 生成的静态图片。三个 Observation Artifact 分别独立物化；四个 Analysis 的 evidence 随整次 run 保留，无需另建 Analysis Artifact identity。具体文件名和编码格式不是稳定语义契约，但所有数值、单位、分组边界、日期与来源须可机器读取并相互对账。当前尚无已执行的 evidence、统计数值或 finding。

| Evidence | 最低语义内容 |
| --- | --- |
| Request / provenance | public Study ID、规范起止日期、run key、四个 family ↔ underlying 映射、上游 public product 与 request/source identity、三个 Observation Artifact identities、固定 predictor 与 horizons。 |
| Sample summary | requested bounds；逐 family 的上市界限、有效历史首末实际日期、basis-date count、20D predictor 首末日期与 count、因 future 不足排除的 basis-date count；common-period 首末实际日期与交集 count。 |
| Historical basis summary | 每 family 的完整有效基差历史 count、mean、median、sample standard deviation、min、max、P10/P20/P40/P50/P60/P80/P90；`daily_non_front_basis > 0` 的 premium count/rate、`< 0` 的 discount count/rate、`= 0` 的单独 count/rate。 |
| Full-history breakpoints / regime table | 每 family 的 P20/P40/P60/P80 阈值及其 20D predictor population count；每 family × Q1–Q5 × horizon 的 count、mean/median/P25/P75 forward return（percentage points）、positive return rate（`[0, 1]` ratio）。 |
| Linear association table | 每 family × horizon 的 count、Pearson correlation、OLS alpha/beta/R²，记录 `null` 所对应的未定义原因。 |
| Common-period breakpoints / regime table | 标记 `population = common_period`；各 family 在同日交集上重新计算的阈值，及与 full-history 表同结构的条件收益统计。 |

历史基差 summary 的 population 是**完整有效 basis history**；full-history regime 和 linear 表的 population 是各 family 的完整 20D predictor sample；common-period 表的 population 是四者的同日交集。这三种分母必须在 metadata、表和报告中分别标明。每个 family × quintile × horizon 均保留一行；空组 `sample_count = 0`，全部条件收益与 positive rate 为 `null`。标准差在少于两条历史 basis observation 时按本 Study 的 Method 为 `null`。以逐日 Observation、样本界限、排除数、阈值和上游 provenance 可以复核每张表；不能把 `null` 表示成零或静默省略。

人类可读 evidence 至少包括样本与限制说明、历史基差摘要、两张分别标识 population 的 regime 表、线性关联表和以下静态图：

1. 各 family 的历史背景图：归一化指数水平与 `daily_non_front_basis` 上下排列、共享时间轴，不使用误导性双 Y 轴。
2. 各 family 的 M0/M1/Q1/Q2 年化 basis 期限结构历史图，用于核对聚合 predictor 是否代表整体期限环境。
3. 各 family 的 quintile × 1D/3D/5D/10D/20D heatmap，median forward return 与 positive return rate 分开展示；空组留空。
4. 使用 common-period 证据的跨 family Q1→Q5 对照图，明确所展示的 horizon 与统计量，用于比较关系方向。

报告引用表与图，不在无实际 evidence 时预写研究结论；可视化舍入不改变 machine-readable 数值。
