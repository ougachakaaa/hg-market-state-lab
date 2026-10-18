# Daily Market Snapshot data authority

本文档从属于 [context architecture](ARCHITECTURE.md)，拥有场景输入、产品专属 Capture scope 与 Raw Artifact contract。共享 Source endpoint 与字段事实由 [Capture authority](../../capture/ARCHITECTURE.md) 拥有。

## 1. 第一版目标与范围

第一版目的非常有限：

> 用最少的数据形成一个能够描述当日 A 股整体市场状态的每日市场数据产品，并验证 Source → Source Capture → Raw Artifact → Analysis Preparation 的完整架构路径。

第一版只使用两个 Tushare 接口：

| Tushare 接口 | 本项目 Source Capture | 用途 |
| --- | --- | --- |
| `index_daily` | `index_daily` | 指数日行情（指数观察 universe） |
| `daily` | `stock_daily` | A 股个股日行情（市场宽度统计） |

Source Capture 名称是本项目语义名称，不要求与 Tushare endpoint 同名（`stock_daily` ↔ `daily` 即一例）。

## 2. 第一版明确不做的事（Non-goals）

数据内容：暂时不加入 `daily_basic`、资金流、融资融券、北向资金、行业、个股基本面、期权、新闻、宏观数据、技术指标。

分析结论：第一版 Analysis-ready Artifact 只表达市场观察事实，不输出 bullish / bearish、risk-on / risk-off、超买 / 超卖、市场情绪评分、后市预测等分析结论。这些属于后续 AI Analysis，不属于本阶段 Analysis Preparation。

派生字段：第一版不加入 advance_ratio / decline_ratio 等比例指标（v1 裁定：breadth 的计数已经直接表达同样信息；若后续需要，先修改本 Guide，再做实现 reconciliation）。

架构机制：不建立通用 universe framework、交易日历系统、scheduler、定时任务、节假日推断、自动 fallback、schema version framework、migration framework、registry 或数据库元数据系统。

## 3. 输入：trade_date

* 目标交易日由调用方给定。
* 脚本层输入使用 `YYYY-MM-DD`，传给 Tushare 时转换为 `YYYYMMDD`。
* 给定日期无数据（非交易日、停市、源无数据）时：属于采集实现需要明确处理的失败/空结果情况。本 Definition 只明确这一边界，不规定具体失败机制；不自动寻找最近交易日，不自动 fallback。

## 4. 产品专属 Capture Scope

本场景使用共享 `index_daily` 与 `stock_daily` Capture。以下只定义本产品的 universe 与 query scope；公共字段、单位和 Raw normalization 不在本文档重复。

### 4.1 `index_daily` scope

#### 指数观察 universe（第一版固定）

以下六个指数代码构成第一版 daily-data_snapshot 场景的指数观察 universe。第一版不做通用 universe framework，只把这组代码作为当前 Analysis Preparation Definition 的明确输入范围。

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

字段与单位见 [Shared Source Capture authority](../../capture/index-stock-contract.md#3-index_daily)。

### 4.2 `stock_daily` scope

#### 查询语义

给定目标交易日，以 `trade_date=YYYYMMDD` 取得 Tushare `daily` 返回的该交易日 A 股日线数据。

第一版 Analysis-ready Artifact 中基于该 Source Capture 计算出来的股票数量，应理解为：

> 当日 `daily` Source Capture 中实际返回并参与统计的股票数量。

不要把它定义成“全部上市股票数量”。

Tushare `daily` 的未复权、停牌缺行、`pre_close` 与 `pct_chg` 语义及字段单位见 [Shared Source Capture authority](../../capture/index-stock-contract.md#4-stock_daily)。本场景不把实际返回并参与统计的数量解释成全部上市股票数量。

## 5. Raw Artifact 文件契约

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

Raw 文件保存采集结果，属于 Analysis Preparation 的输入。Raw 层不按最终 Analysis-ready Artifact 的分类方式重新组织数据。

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
* 为某个 Analysis-ready Artifact schema 大量重构源数据。

Raw Artifact 应尽量保留 Source 返回数据的原始语义。

### 执行边界

Raw 文件的写入、覆盖与重跑策略属于采集实现细节，本 Definition 不预设；无数据交易日的处理边界见第 3 节，Raw → Analysis-ready Artifact 的依赖边界见第 7 节。
