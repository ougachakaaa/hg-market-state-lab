# IM Basis Forward Return Association results authority

本文档是本 Study retained evidence contract 的唯一 canonical owner；Study identity 与 request 见 [Study entry](ARCHITECTURE.md)，Observation、Analysis、公式与 analytical validity 见 [Method](METHOD.md)。当前尚未运行真实研究，没有已执行统计结果、plot 或 finding；不得填入 placeholder 数值或推测结论。

## Retained evidence

两个 named Observations 与两个 named Analyses 是 Study-local semantic components；V1 不要求独立 materialized 或 retained component Artifacts。每次成功 retained run 至少产生 machine-readable result、human-readable report/table 与 static visualization。具体 filename、serialization 与组件内部表示不是稳定语义契约，但机器可读证据必须包含下列最低结构，供人复核整次研究：

```text
Sample / provenance summary
    requested_start_trade_date
    requested_end_trade_date
    effective_predictor_start_trade_date
    effective_predictor_end_trade_date
    source_observation_count
    common_sample_count
    future_support_only_count
    horizons = 1, 3, 5, 10, 15, 20 trading observations
    predictor identity = non_front_mean_basis

Quintile breakpoint evidence
    P20
    P40
    P60
    P80

Association summary table: one row per horizon
    horizon
    sample_count
    pearson_correlation
    ols_alpha
    ols_beta
    ols_r_squared

Quintile table: one row per basis_quintile × horizon
    basis_quintile
    horizon
    sample_count
    mean_forward_return_pct
    median_forward_return_pct
    positive_return_rate
```

`requested_*` 是规范化的 inclusive Study request dates；`effective_predictor_*` 是共同样本中的首末实际 trade dates。`source_observation_count` 是完整 Snapshot result 中不同 CSI1000 实际 observation dates 数；`common_sample_count` 是 [Method](METHOD.md) 定义的共享 eligible predictor dates 数；`future_support_only_count` 是输入尾部仅为较早日期提供 future support、未进入共同 predictor sample 的日期数。六个 association rows 的 `sample_count` 均等于 `common_sample_count`；每个 horizon 的五个 quintile row counts 之和也等于它，且每个 quintile 非空。同一个 quintile 的 sample count 在六个 horizon 中相同。

在成功 run 中，Snapshot result 构成本次请求的完整、有序实际交易 observation sequence，每个日期满足上游四槽 panel 与 close contract，且共同样本严格采用完整 20D future support。在这些前提下，尾部恰有 20 个 support-only dates，必须满足：

```text
future_support_only_count = 20
source_observation_count = common_sample_count + future_support_only_count
```

Retained evidence 必须能据此复核 sample path，且保留当次 P20/P40/P60/P80 的实际 numeric boundaries；仅有 Q1–Q5 label 不足以复核分组。阈值 ties 导致 empty quintile、无定义统计量、无效样本或上游 contract violation 属于整次 run failure，不以空表、`null`、NaN、推测值或缩短的 horizon set 表示成功结果。失败不发布部分 retained evidence；已存在 run 的碰撞与替换保护由 [Research UI authority](../../ui/ARCHITECTURE.md) 拥有。

## Units、human presentation 与解释

Human-readable report/table 应标明请求区间、有效 predictor 区间、predictor identity、六个 trading-observation horizons、样本量与各统计量单位，使 association summary、numeric quintile boundaries 和 quintile table 可与机器可读结果对照。`non_front_mean_basis` 与 P20/P40/P60/P80 的单位为 annualized percentage points；`forward_return_h_pct`、OLS alpha、mean/median forward return 的单位为 percentage points；OLS beta 为 forward-return percentage points / annualized-basis percentage point；Pearson correlation、OLS R² 与 `positive_return_rate` 无量纲，后者表达 0–1 的 historical empirical rate。`sample_count` 与 `horizon` 分别标为 observations 与 trading observations。

至少保留一张静态 Research visualization，展示 predictor-vs-forward-return scatter 与 simple OLS line、correlation-by-horizon，或 quintile forward-return comparison 中的一种。图形应标明所展示的 horizon、适用的 basis / return 单位和必要的 sample context；它只是 Research evidence presentation，不是 production UI。

Retained result 是 exploratory Research Evidence。`positive_return_rate` 必须呈现为 historical empirical conditional rate，不得称为 forecast probability；报告、表格和图形不作未经校正的显著性、因果、out-of-sample predictive power 或交易结论，也不得直接输出 forecast、expected-return signal、forward-looking probability、confidence、model score 或 trading action。
