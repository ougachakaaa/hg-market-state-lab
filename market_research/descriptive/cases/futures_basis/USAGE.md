# Futures Basis statistics usage

Usage-only; semantics enter through [Case](ARCHITECTURE.md) and
[analysis contract](STATISTICS_API.md). Run from repository root's Poetry environment.
The following is a real-market Python example; public preparation may obtain missing
facts through the configured DataLake services. All dates and numerical parameters
are explicit. Existing WP3 observations can be passed directly instead.

```python
from datetime import date
from market_statistics import QuantileSpec, IntervalCountSpec
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest, DistributionRequest, ComparisonRequest,
    observe_futures_basis, analyze_distribution, compare_terms, discount_runs,
)

start, end = date(2026, 10, 12), date(2026, 10, 23)
observations = observe_futures_basis(FuturesBasisRequest("IM", start, end))
points = QuantileSpec([0, .25, .5, .75, 1])
edges = IntervalCountSpec([-1000, -500, -100, 0, 100, 500, 1000], "index_points")
request = DistributionRequest("im-m0-basis", "M0", "basis_value", start, end, points, edges)
result = analyze_distribution(observations, request)
print([(m.spec, m.result, m.failure_category, m.reason) for m in result.methods])
print({s: result.count(s) for s in ("eligible", "unavailable", "excluded", "not_applicable")})
print([r.identity for r in result.binding])
print(result.source.prepared.input_fingerprint)
comparison = compare_terms(observations, ComparisonRequest(
    "im-m0-m1-basis", ("M0", "M1"), "basis_value", start, end, points, edges,
))
print(comparison.common_dates, comparison.dropped)
runs = discount_runs(observations, "M0", start, end)
print(runs.complete, runs.censored)
```

For `basis_ratio` or `annualized_basis_ratio`, explicitly supply edges in
`decimal_ratio`, e.g. `[-1, -.1, -.01, 0, .01, .1, 1]`. The three methods are
Mean, Quantile and IntervalCount, in that order. There are no default quantile
points or edges. Inspect each method's failure_category before interpreting it.
Empty eligibility gives `no_eligible_sample`; histogram outside counts retain the
full eligible denominator. Annualized expiry days are Not Applicable.

`source.prepared` exposes separate CFFEX/SSE natural-date coverage, Futures
product-day and Index-session coverage and original proofs. `source.accounting`
contains base and all metric populations for the full source window; distribution
`candidates` and `count` cover the requested analysis subwindow. Every candidate
retains status/reason and original Contract-day/source references. Comparisons'
`candidates` and `dropped` retain both sides' original outcomes; both computed
populations use exactly `common_dates`.

Complete runs and censored fragments are separate collections. The fragment's
observed session count is a lower bound, not a complete duration. Slots share
underlyings/dates; neither daily levels nor runs assert independent draws. This
short window is an E2E check and supports no long-term inference.

The earlier WP4 cache replay remains test infrastructure, documented in
[WP4 acceptance](WP4_ACCEPTANCE.md). WP5 adds the independent formal offline
delivery below; no lab command, HTTP endpoint or publication lifecycle is added.

## WP5 一次执行并交付报告

从 repository root 执行。输出必须是仓库外尚不存在的新目录；以下研究参数均为显式输入，
不是默认值。首次获取行情需要现有 DataLake provider 配置；只读重放不需要凭证或网络。

```bash
poetry run python market_research/scripts/futures_basis_report.py \
  --product IM --start 2026-10-12 --end 2026-10-23 \
  --quantile-points '[0,0.25,0.5,0.75,1]' \
  --basis-value-edges '[-1000,-500,-100,0,100,500,1000]' \
  --basis-ratio-edges '[-1,-0.1,-0.01,0,0.01,0.1,1]' \
  --annualized-basis-ratio-edges '[-10,-1,-0.1,0,0.1,1,10]' \
  --output /tmp/im-basis-report-new
```

生成需要根 Poetry 环境、Node 及已安装的 `ui_web/node_modules`。命令成功后双击
`/tmp/im-basis-report-new/report.html`，无需启动服务。HTML 可单独复制离线阅读；
审计和复现时保留整个目录。原始值使用 index_points / decimal_ratio，不自动缩放。

长期候选将日期明确改为 `--start 2024-01-01 --end 2026-10-30`，并使用另一个新输出目录。
缺失或失败不会被短样本替代；输入完整性不通过时仅输出诊断包并返回非零状态。
数值方法失败会输出 partial 报告；空样本标记 `no_eligible_sample`。

如果已有正式保留输入，在相同参数后增加
`--inputs /absolute/path/inputs.canonical.json`；这条路径禁止 Source/cache 访问，
必须与显式 Product、Window 完全匹配。它不接受 WP4 测试结果 JSON。

```bash
poetry run python market_research/scripts/futures_basis_report.py verify /tmp/im-basis-report-new
poetry run python market_research/scripts/futures_basis_report.py replay /tmp/im-basis-report-new
```

verify 校验包内摘要、版本、指纹与关联；replay 从保留的公共 inputs 重新执行既有构建与
统计并比较结果。都不访问 Source、HTTP 或 SQLite。篡改、未知版本、缺文件或重放差异返回非零。
实际方法失败可能不可重复；其原始失败仍保留。详细契约见 [Evidence](EVIDENCE.md)，
真实验收及作品集路径见 [WP5 acceptance](WP5_ACCEPTANCE.md)。
