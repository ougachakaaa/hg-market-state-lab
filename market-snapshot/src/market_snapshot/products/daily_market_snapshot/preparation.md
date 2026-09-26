# Daily Market Snapshot preparation authority

本文档从属于 [context architecture](ARCHITECTURE.md)，拥有场景 Raw → analysis-ready artifact 的结构、公式、失败边界与可复现性。输入与 Raw contract 见 [data.md](data.md)。

## 6. 第一版 Analysis Preparation Definition

### 输出位置与形态

```text
data/snapshots/
└─ YYYY-MM-DD/
   └─ snapshot.json
```

第一版只需要一个 JSON 文件，不提前拆分成多个文件。

### 逻辑结构

```text
snapshot
├─ trade_date
├─ indices
└─ breadth
```

### JSON 形态（语义示意，数值为占位示例）

```json
{
  "trade_date": "2026-09-17",
  "indices": {
    "000016.SH": {
      "open": 2688.29,
      "high": 2715.45,
      "low": 2681.12,
      "close": 2703.87,
      "pre_close": 2690.55,
      "change": 13.32,
      "pct_chg": 0.5,
      "vol": 51234567.0,
      "amount": 52123456.78
    },
    "...": {}
  },
  "breadth": {
    "traded_stocks": 5321,
    "advancers": 2803,
    "decliners": 2314,
    "unchanged": 204,
    "up_3pct_or_more": 512,
    "down_3pct_or_more": 348,
    "up_5pct_or_more": 187,
    "down_5pct_or_more": 96,
    "total_amount": 812345678.9
  }
}
```

### 6.1 indices

* 来源：`index_daily` Raw Artifact。
* 按指数代码组织：对象 key 即指数 `ts_code`，identity 由 key 表达，对象内部不再重复携带 `ts_code`。
* `indices` 必须包含data authority 第 4.1 节列出的全部六个指数；缺失任一只指数属于 Raw 不符合预期，不完整的 Raw 不能用于产出第一版 Analysis-ready Artifact。
* 每个指数包含以下字段，语义与单位沿用 Raw（见 data authority 4.1）：`open`、`high`、`low`、`close`、`pre_close`、`change`、`pct_chg`、`vol`（手）、`amount`（千元）。
* 不增加技术指标或趋势评价。

### 6.2 breadth

* 来源：`stock_daily` Raw Artifact。
* 用途：当日 A 股横截面的简单市场宽度统计。

| 字段 | 定义 | 说明 |
| --- | --- | --- |
| `traded_stocks` | 当日 `stock_daily` 实际返回的记录数 | 计数口径见 4.2 |
| `advancers` | `pct_chg > 0` 的记录数 | 上涨家数 |
| `decliners` | `pct_chg < 0` 的记录数 | 下跌家数 |
| `unchanged` | `pct_chg == 0` 的记录数 | 平盘家数 |
| `up_3pct_or_more` | `pct_chg >= 3` 的记录数 | 涨幅 ≥ 3% |
| `down_3pct_or_more` | `pct_chg <= -3` 的记录数 | 跌幅 ≥ 3% |
| `up_5pct_or_more` | `pct_chg >= 5` 的记录数 | 涨幅 ≥ 5% |
| `down_5pct_or_more` | `pct_chg <= -5` 的记录数 | 跌幅 ≥ 5% |
| `total_amount` | 当日 `stock_daily.amount` 求和 | 单位：千元（保留 Tushare 来源单位） |

不变式（必须成立）：

```text
advancers + decliners + unchanged = traded_stocks
```

* `pct_chg` 的比较基于 Source 数值（百分比数值，例如 `pct_chg = 3.5` 表示 +3.5%）。
* 若 Raw 中 `pct_chg` 或 `amount` 缺失、不符合预期，不得静默跳过记录或估算数值——breadth 各字段按本节定义基于当日全部记录计算。
* `total_amount` 保留千元单位。Analysis-ready Artifact 中不得出现无法判断单位的金额语义。

## 7. Analysis-ready Artifact 与 Raw 的依赖关系

```text
Tushare index_daily
        ↓
Raw index_daily
        ┐
        │
        ├──→ Analysis Preparation → snapshot.json
        │
Raw stock_daily
        ↑
Tushare daily
```

Analysis Preparation 只能消费已有 Raw Artifact，不得自己直接调用 Tushare。这是本阶段必须保持的架构边界。

## 8. 可复现性

对于同一个：

* Analysis Preparation Definition（本文档）；
* `trade_date`；
* Raw Artifact 内容；

Analysis Preparation 应产生语义一致的结果。

当前不建立 schema version framework、migration framework、registry 或数据库元数据系统。本文档即第一版 Analysis Preparation Definition authority；以后数据需求变化时，先修改对应 authority，再对实现做 reconciliation。

## 9. 实现约束

本文档是第一版 daily-market-snapshot 场景的 Analysis Preparation Definition authority。各职责如下：

```text
trade_date
   ↓
Source Capture index_daily → data/raw/YYYY-MM-DD/index_daily.json
Source Capture stock_daily → data/raw/YYYY-MM-DD/stock_daily.json
   ↓
Analysis Preparation → data/snapshots/YYYY-MM-DD/snapshot.json
```

Source Capture 职责：调用 Tushare 对应 endpoint、按本文档 universe 选择范围、minimal normalization，写出 Raw Artifact。Analysis Preparation 职责：只消费上述 Raw Artifact，按本文档第 6 节组装 breadth / indices，写出 Analysis-ready Artifact；不得调用 Tushare。

实现不得超出本文档、[Shared Source Capture authority](../../capture/ARCHITECTURE.md) 与 [模块架构](../../../../ARCHITECTURE.md) 的范围。实现状态和代码位置不属于本文档的稳定语义。
