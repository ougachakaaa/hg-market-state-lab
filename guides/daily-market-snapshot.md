# guides/daily-market-snapshot.md — 第一版 Daily Snapshot Definition

> 状态：当前生效。本文档是第一版 Daily Snapshot 的 Definition authority。
>
> 层级：本文档位于 `ARCHITECTURE.md` 之下，定义第一版 Snapshot 的具体数据需求、Dataset 语义、Raw 契约、Snapshot 输出结构与执行边界。架构层面的稳定边界以 `ARCHITECTURE.md` 为准；本文档不得与其冲突。
>
> 实现本 Guide 任务的 Agent 应先阅读 `ARCHITECTURE.md` 第 2、3 节（核心架构与 Raw/Snapshot 边界）、第 4 节（架构边界的执行）与第 9 节（项目结构），再按本文档执行。

## 1. 第一版目标与范围

第一版目的非常有限：

> 用最少的数据形成一个能够描述当日 A 股整体市场状态的 Daily Market Snapshot，并验证 Source → Raw Dataset → Snapshot 的完整架构路径。

第一版只使用两个 Tushare 接口：

| Tushare 接口 | 本项目 Dataset | 用途 |
| --- | --- | --- |
| `index_daily` | `index_daily` | 指数日行情（指数观察 universe） |
| `daily` | `stock_daily` | A 股个股日行情（市场宽度统计） |

Dataset 名称是本项目语义名称，不要求与 Tushare endpoint 同名（`stock_daily` ↔ `daily` 即一例）。

## 2. 第一版明确不做的事（Non-goals）

数据内容：暂时不加入 `daily_basic`、资金流、融资融券、北向资金、行业、个股基本面、期权、新闻、宏观数据、技术指标。

分析结论：第一版 Snapshot 只表达市场观察事实，不输出 bullish / bearish、risk-on / risk-off、超买 / 超卖、市场情绪评分、后市预测等分析结论。这些属于后续 AI Analysis，不属于本阶段 Snapshot Assembly。

派生字段：第一版不加入 advance_ratio / decline_ratio 等比例指标（v1 裁定：breadth 的计数已经直接表达同样信息；若后续需要，先修改本 Guide，再做实现 reconciliation）。

架构机制：不建立通用 universe framework、交易日历系统、scheduler、定时任务、节假日推断、自动 fallback、schema version framework、migration framework、Snapshot registry 或数据库元数据系统。

## 3. 输入：trade_date

* 目标交易日由调用方给定。
* 脚本层输入使用 `YYYY-MM-DD`，传给 Tushare 时转换为 `YYYYMMDD`。
* 给定日期无数据（非交易日、停市、源无数据）时：属于采集实现需要明确处理的失败/空结果情况。本 Definition 只明确这一边界，不规定具体失败机制；不自动寻找最近交易日，不自动 fallback。

## 4. Dataset 定义

### 4.1 Dataset: index_daily

* 语义名称：`index_daily`
* Source：Tushare `index_daily`

#### 指数观察 universe（第一版固定）

以下六个指数代码构成第一版 Snapshot 的指数观察 universe。第一版不做通用 universe framework，只把这组代码作为当前 Snapshot Definition 的明确输入范围。

| ts_code | 指数 |
| --- | --- |
| `000016.SH` | 上证50 |
| `000300.SH` | 沪深300 |
| `000905.SH` | 中证500 |
| `000852.SH` | 中证1000 |
| `399006.SZ` | 创业板指 |
| `000688.SH` | 科创50 |

#### 查询语义

对目标交易日（传给 Tushare 时为 `YYYYMMDD`），分别取得上述每一个指数在该交易日的 `index_daily` 数据。

#### 核心字段语义

| 字段 | 语义 | 单位/说明 |
| --- | --- | --- |
| `ts_code` | 指数代码 | 源主键 |
| `trade_date` | 交易日 | Raw 层统一为 `YYYY-MM-DD` |
| `open` | 开盘价 | 点 |
| `high` | 最高价 | 点 |
| `low` | 最低价 | 点 |
| `close` | 收盘价 | 点 |
| `pre_close` | 昨收价 | 点 |
| `change` | 涨跌额 | 点，源定义 = close − pre_close |
| `pct_chg` | 涨跌幅 | %（数值 1 表示 1%） |
| `vol` | 成交量 | 手（保留 Tushare 原始单位） |
| `amount` | 成交额 | 千元（保留 Tushare 原始单位） |

本阶段不做没有业务需要的额外派生指标。

### 4.2 Dataset: stock_daily

* 语义名称：`stock_daily`
* Source：Tushare `daily`（注意与 Dataset 名称不同名）

#### 查询语义

给定目标交易日，以 `trade_date=YYYYMMDD` 取得 Tushare `daily` 返回的该交易日 A 股日线数据。

#### 数据语义注意

Tushare `daily` 是未复权日行情；停牌期间不会返回对应股票数据。

`pre_close` 是昨收价（除权价）：除权除息日按交易所口径给出除权参考价，不是简单的未复权昨收。`pct_chg` 保持为 Tushare Source 提供的涨跌幅事实，不在 Raw 层重算或改写。

因此第一版 Snapshot 中基于该 Dataset 计算出来的股票数量，应理解为：

> 当日 `daily` Dataset 中实际返回并参与统计的股票数量。

不要把它定义成“全部上市股票数量”。

#### 核心字段语义

| 字段 | 语义 | 单位/说明 |
| --- | --- | --- |
| `ts_code` | 股票代码 | 源主键 |
| `trade_date` | 交易日 | Raw 层统一为 `YYYY-MM-DD` |
| `open` | 开盘价 | 元（未复权） |
| `high` | 最高价 | 元（未复权） |
| `low` | 最低价 | 元（未复权） |
| `close` | 收盘价 | 元（未复权） |
| `pre_close` | 昨收价（除权价） | 元；除权除息日为交易所口径的除权参考价 |
| `change` | 涨跌额 | 元，源定义 = close − pre_close |
| `pct_chg` | 涨跌幅 | %（数值 1 表示 1%） |
| `vol` | 成交量 | 手 |
| `amount` | 成交额 | 千元 |

本阶段 Raw Dataset 保留事实数据，不提前塞入市场判断。

## 5. Raw Dataset 文件契约

第一版采用按交易日目录组织：

```text
data/raw/
└─ YYYY-MM-DD/
   ├─ index_daily.json
   └─ stock_daily.json
```

例如：

```text
data/raw/
└─ 2026-09-17/
   ├─ index_daily.json
   └─ stock_daily.json
```

### Raw 是 Source Fact

Raw 文件保存采集结果，属于 Snapshot Assembly 的输入。Raw 层不按最终 Snapshot 的分类方式重新组织数据。

### 文件形态

每个 Raw 文件是一个 JSON 数组，数组中每个元素对应 Source 返回的一行记录，字段名与 Source 字段一致（见第 4 节字段表），并原样保留 Source 返回的全部行。

### Minimal Normalization

第一阶段允许为了 JSON 文件生成进行必要的最小转换：

* DataFrame → JSON-compatible records；
* 日期表达统一（`trade_date` 统一为 `YYYY-MM-DD`）；
* numpy scalar → JSON scalar。

不允许：

* 在 Raw 层计算 breadth；
* 在 Raw 层重新定义市场分类；
* 在 Raw 层生成分析结论；
* 为某个 Snapshot schema 大量重构源数据。

Raw Dataset 应尽量保留 Source 返回数据的原始语义。

### 执行边界

Raw 文件的写入、覆盖与重跑策略属于采集实现细节，本 Definition 不预设；无数据交易日的处理边界见第 3 节，Raw → Snapshot 的依赖边界见第 7 节。

## 6. 第一版 Snapshot Definition

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

* 来源：`index_daily` Raw Dataset。
* 按指数代码组织：对象 key 即指数 `ts_code`，identity 由 key 表达，对象内部不再重复携带 `ts_code`。
* `indices` 必须包含第 4.1 节列出的全部六个指数；缺失任一只指数属于 Raw 不符合预期，不完整的 Raw 不能用于产出第一版 Snapshot。
* 每个指数包含以下字段，语义与单位沿用 Raw（见 4.1）：`open`、`high`、`low`、`close`、`pre_close`、`change`、`pct_chg`、`vol`（手）、`amount`（千元）。
* 不增加技术指标或趋势评价。

### 6.2 breadth

* 来源：`stock_daily` Raw Dataset。
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
* `total_amount` 保留千元单位。Snapshot 中不得出现无法判断单位的金额语义。

## 7. Snapshot 与 Raw 的依赖关系

```text
Tushare index_daily
        ↓
Raw index_daily
        ┐
        │
        ├──→ Snapshot Assembly → snapshot.json
        │
Raw stock_daily
        ↑
Tushare daily
```

Snapshot Builder 只能消费已有 Raw Dataset，不得自己直接调用 Tushare。这是本阶段必须保持的架构边界。

## 8. 可复现性

对于同一个：

* Snapshot Definition（本文档）；
* `trade_date`；
* Raw Dataset 内容；

Snapshot Assembly 应产生语义一致的结果。

当前不建立 schema version framework、migration framework、Snapshot registry 或数据库元数据系统。本文档即第一版 Snapshot Definition authority；以后 Snapshot 需求变化时，先修改对应 authority，再对实现做 reconciliation。

## 9. 下一步实现范围

本文档是第一版的设计 authority；实现阶段按本文档与 `ARCHITECTURE.md` 交付：

```text
trade_date
   ↓
采集 index_daily → data/raw/YYYY-MM-DD/index_daily.json
采集 stock_daily → data/raw/YYYY-MM-DD/stock_daily.json
   ↓
Snapshot Assembly → data/snapshots/YYYY-MM-DD/snapshot.json
```

实现对应 `ARCHITECTURE.md` 第 9 节的脚本约定（`scripts/fetch_*.py` 负责采集单个 Dataset 并写出 Raw Dataset；`scripts/build_snapshot.py` 负责 Snapshot Assembly），并配套 `tests/` 测试。

本文档不包含实现细节；实现不得超出本文档与 `ARCHITECTURE.md` 的范围。
