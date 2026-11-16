# Frontend presentation formatting authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md) 与
[presentation architecture](presentation-architecture.md)，拥有所有 `ui_web` surface
共用的用户可见数值与时间格式策略。具体 feature 仍拥有其 metric、label、missing
文案与 visual encoding；本文件只规定既有 fact 如何以文本和图表刻度呈现。

Production、Static Demo 与 offline reader 共用同一策略。该策略不改变 wire
contract、原始数值、坐标、排序、null/zero/absence 语义、identity 或任何后端计算。

## 1. 时间

- `date-time` 时间点（例如 `checked_at`、`created_at`、`started_at`、
  `finished_at`）必须以 `Asia/Shanghai`（北京时间）显示为
  `YYYY-MM-DD HH:mm:ss（北京时间）`，与浏览器本地时区无关。
- 只接受带 `Z` 或 `±HH:mm` offset 的有效 `date-time`；缺失或非法值使用调用方提供
  的 missing 文本。
- `date`（`trade_date`、`expiry_date`、`delist_date`、`market_date` 等日历日期）
  保持 canonical `YYYY-MM-DD`，不进行时区转换，也不补出时间。
- 共享实现为 `src/shared/format/time.ts` 的 `formatBeijingTime` 与
  `BEIJING_TIME_ZONE`。新 surface 不得自行使用 `toLocaleString()` 或本地时区。

## 2. 比例

所有用户可见比例显示为百分数，固定 1 位小数，并保留负号：

```text
0.15342   -> 15.3%
-0.0868   -> -8.7%
0         -> 0.0%
1         -> 100.0%
-0        -> 0.0%
```

适用范围包括 `decimal_ratio`、probability、frequency、coverage ratio 与
percentile rank。禁止继续以 `0.15342`、`15.342%` 或 6 位小数等形式显示这些值。
`-0` 与四舍五入后的负零必须归一为 `0.0%`。

## 3. 非整数数值

不属于必然整数的数值固定 2 位小数，包括价格、strike、基差/价差点数、premium
points、quantile/mean/min/max、区间边界及图表刻度。整数也显示为 `.00`，例如：

```text
7000      -> 7000.00
7312.456  -> 7312.46
-12.3     -> -12.30
0         -> 0.00
```

必然整数保持整数，不显示小数：N、sample/candidate/outcome counts、DTE、
delta days、sessions、roll count、jobs/analyses counts、bytes 与同类计数字段。

技术数值不使用千分位分组；图表、表格与 hover 使用同一数字文本。货币金额仍使用
现有货币格式（人民币符号、2 位小数与既有分组）。

## 4. 图表

- ratio axis → Plotly `tickformat` / `hoverformat` 为 `.1%`
- count axis → `d`
- 其他 numeric axis → `.2f`
- hover、annotation、legend、table 与普通文本共用第 2、3 节规则。
- 原始 trace data、坐标、bin edges 与排序不得因 display formatting 而改变。
- category identity 必须与显示 label 分离。多个 bin 的 rounded label 相同时，
  仍须用独立 raw category identity / `tickvals` 保留每个真实 bin 和 bar。

严格 1 位小数百分比意味着极近的区间边界可能显示相同文本；这只能是 label
重合，不能变成数据合并、去重或重新分箱。

## 5. 例外

以下内容不使用显示格式化，继续保留原始值或原始文本：

- Raw JSON、Raw HTTP Response Inspector、Context JSON；
- CSV（包括 yield 的 decimal ratio）；
- `Raw value` 等明确标注 raw/evidence 的明细；
- ID、hash、fingerprint、版本字符串、request echo、单位字符串；
- 控件配置与选项标签（例如 `±400 点`、分箱宽度 `0.1 个百分点`）；
- 日期型值（第 1 节）；
- missing / unavailable / absence 的既有文案与语义。

## 6. 共享实现

- `src/shared/format/number.ts`：`formatPercent`、`formatDecimal`、
  `formatInteger`。
- `src/shared/format/time.ts`：`formatBeijingTime`、`BEIJING_TIME_ZONE`。
- `src/shared/format/unit.ts`：按显式 unit 分派 ratio / count / decimal / plain，
  供 generic Visualization、IntervalCount 与文件级统计投影共用。
- `src/shared/visualization/presentation.ts`：`plotlyAxisFormat` 把同一 unit
  分类映射为 Plotly format。

Feature-local 格式化可以保留，但必须委托给上述 helper 或产生同等且不冲突的结果。
Shared helper 不携带产品语义，也不得改变原始 fact。

## 7. 当前 surface 对照

| Surface | 时间 | 比例 | 非整数 / 整数 |
| --- | --- | --- | --- |
| Backtesting | Run `created_at` / `started_at` / `finished_at` 北京时间 | 收益、回撤、超额 1 位 % | 货币 2 位；roll count 整数 |
| Futures Basis Research | preflight `checked_at`、Run `created_at` 北京时间 | basis ratio、frequency、probability 1 位 % | index points 2 位；counts 整数 |
| Futures Calendar Spread | date-only | annualized spread ratio 1 位 % | spread points / close 2 位；DTE、delta days 整数 |
| Calendar Spread Relative Value | date-only | metric ratio、percentile、frequency 1 位 % | metric points / close 2 位；N、DTE 整数 |
| MO Option Chain | date-only | 无 | price / strike / spot / futures 2 位；counts 整数 |
| MO Premium Plane | date-only | yield 1 位 % | points / price / strike 2 位；DTE 整数 |
| Research Explorer | date-only | probability、frequency、coverage 1 位 % | 统计值按 unit；counts 整数 |

历史 acceptance 文档记录当时行为，不因本策略回写；当前 authority、实现和可执行
测试以本文件为准。
