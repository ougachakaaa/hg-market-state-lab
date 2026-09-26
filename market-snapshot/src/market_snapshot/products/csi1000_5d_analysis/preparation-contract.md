# CSI1000 5D Analysis Preparation authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有五个 goal-scoped Raw Artifacts 到 analysis-ready `snapshot.json` 的窗口、join、投影、公式、排序、null 与失败语义。输入契约见 [data.md](data.md)；本文档不执行业务分析。

## 1. 目标与范围

本场景的分析目的不变（以某个目标交易日为观察基准，为外部分析器提供足够数据以分析未来约 5 个交易日的中证1000市场状态），但本文档只负责其中一段：

```text
Raw Artifact（五个 Raw artifacts）
        ↓
deterministic Analysis Preparation
        ↓
analysis-ready local file（snapshot.json）
```

本文档是这段过程的 Definition authority，回答：

* 五个 Raw Artifact 如何组成一个 analysis-ready Artifact；
* 最终文件写到哪里；
* CSI1000 使用多少历史数据；
* 第一版具体有哪些 derived fields，以及每个字段的输入、公式与单位；
* MO basic + daily 如何组合；
* IM basic + daily + CSI1000 如何组合；
* 哪些数据属于 deterministic transformation；
* 哪些结论严格属于 external analyzer。

本文档**不**实现，也**不**重新定义 `data.md` 已锁定的 Source / Source Capture / Raw Artifact 契约。任何与 Raw 契约重复的定义以 `data.md` 为准。

## 2. 职责边界：确定性数据转换 vs 业务分析

### 2.1 本项目允许（deterministic transformation）

输入相同则结果固定的确定性数据转换。第一版 Analysis Preparation 允许包含：

```text
returns
moving averages
rolling high / low
ATR
realized volatility

option moneyness / strike 位置
normalized premium
days to expiry

IM basis
annualized basis
days to delist
```

这些都是对已有 Raw Fact 的确定性组织/计算，不引入业务判断。

### 2.2 本项目不负责（业务分析，属于 external analyzer）

Analysis-ready Artifact 禁止输出以下结论类字段，即使它们"很好算"：

```text
center / 未来5日中枢
noise_zone / 噪声区
upper_reversal_zone / lower_reversal_zone

market_regime
trend_strength
overbought / oversold

sell_call / sell_put
cheap / expensive
recommended strike

probability_up / probability_down
confidence
recommendation
```

以及任何 bullish / bearish、反转概率、交易建议、目标点位等结论。这些始终属于 analyzer。

### 2.3 输出语义

最终 `snapshot.json` 必须满足：

```text
structured
reproducible
analysis-ready
```

即外部分析器不需要重新理解 Source 的杂乱结构、也不需要从 60 日历史中自行重建期限结构，即可直接消费。

## 3. 输入与输出

### 3.1 输入

Analysis Preparation 只依赖：

```text
target_trade_date

data/raw/csi1000-5d-analysis/<target_trade_date>/
    index_daily_history.json
    mo_option_basic.json
    mo_option_daily.json
    im_futures_basic.json
    im_futures_daily.json

当前 Analysis Preparation Definition（本文档）
```

### 3.2 输出

Data Service canonical user-facing output：

```text
output/
└─ csi1000-5d-analysis/
   └─ YYYY-MM-DD/
      └─ snapshot.json
```

`YYYY-MM-DD` 表示 `target_trade_date`（目录名是目标交易日，不是文件中所有记录共同的 `trade_date`）。第一版只使用一个 JSON 文件，不提前拆分多个文件，不引入 schema registry 或 version framework。

`snapshot.json` 是 Data Service `csi1000-5d-analysis` 的最终 artifact，其 canonical user-facing output 锁定为 `output/csi1000-5d-analysis/<target_trade_date>/snapshot.json`（见 [Data Service delivery](../../services/delivery.md)）。本文档定义的是 `snapshot.json` 的**内容与组织方式**；Analysis Preparation 按本文档产出该内容，由本产品的 Service orchestration 发布到该 canonical 位置，不再写 `data/snapshots/...`，不维护两份 artifact。

## 4. 输出逻辑结构

```text
snapshot
├─ target_trade_date
├─ underlying
├─ mo_options
└─ im_futures
```

* `underlying`：表达 CSI1000（`000852.SH`）的历史与派生指标；
* `mo_options`：表达目标交易日 MO option chain；
* `im_futures`：表达近期 IM term-structure facts。

## 5. underlying

### 5.1 输入与窗口选择

输入：`index_daily_history.json`（Source Capture `index_daily`，`000852.SH`）。

Analysis Preparation 精确选择：

```text
latest 120 distinct trading rows
whose trade_date <= target_trade_date
```

要求：

```text
恰好 120 个交易日
最后一行 = target_trade_date
按 trade_date ascending
```

不足 120 日，或 `trade_date == target_trade_date` 缺失，则 Analysis Preparation 失败。

### 5.2 输出形态

```text
underlying:
    ts_code
    history
    derived
```

* `ts_code`：固定为 `"000852.SH"`。identity 由该字段表达，`history` 内每行不再重复携带 `ts_code`。
* `history`：上述 120 行，每行保留以下字段，语义与单位沿用 Raw（见 [Shared Source Capture authority](../../capture/ARCHITECTURE.md)）：

```text
trade_date
open
high
low
close
pre_close
change
pct_chg
vol
amount
```

* `derived`：单层对象，保存第 6 节定义的、以 `target_trade_date` 为终点的标量派生指标。

### 5.3 目标日收盘价

`underlying_close`（供 `mo_options` 与 `im_futures` 使用）定义为：

```text
underlying.history 最后一行（trade_date == target_trade_date）的 close
```

它是历史窗口中的既有 Fact，不是重新计算或从其他日期补出的值。Analysis-ready Artifact 中需要 `underlying_close` 的位置必须与此值一致，不得出现两个不同的"目标日收盘价"。

## 6. underlying derived fields

第一版只锁定以下 11 个标量字段，全部以 `target_trade_date`（记为 `t`）为终点，从 `underlying.history` 计算。不为了"可能有用"增加更多技术指标。

记 `close_i` / `high_i` / `low_i` / `pre_close_i` 为 `history` 中第 `i` 个交易日的对应值（按 `trade_date` 升序，`t` 为最后一行）。

### 6.1 return_Nd_pct

| 字段 | 公式 | 单位 |
| --- | --- | --- |
| `return_1d_pct` | `(close_t / close_{t-1} - 1) * 100` | percentage points |
| `return_5d_pct` | `(close_t / close_{t-5} - 1) * 100` | percentage points |
| `return_20d_pct` | `(close_t / close_{t-20} - 1) * 100` | percentage points |

`N` 表示 N 个交易日跨度；`close_{t-N}` 是 `history` 中在 `t` 之前第 N 个交易日的 close。该字段由 close 独立计算，不使用 Source 的 `pct_chg`。

### 6.2 SMA

| 字段 | 公式 | 单位 |
| --- | --- | --- |
| `sma_5` | `mean(close_{t-4}, ..., close_t)`（5 个） | index points |
| `sma_20` | `mean(close_{t-19}, ..., close_t)`（20 个） | index points |
| `sma_60` | `mean(close_{t-59}, ..., close_t)`（60 个） | index points |

### 6.3 rolling high / low

| 字段 | 公式 | 单位 |
| --- | --- | --- |
| `rolling_high_20` | `max(high_{t-19}, ..., high_t)` | index points |
| `rolling_low_20` | `min(low_{t-19}, ..., low_t)` | index points |

### 6.4 ATR 14

先定义每日 True Range：

```text
TR_i = max(
    high_i - low_i,
    abs(high_i - pre_close_i),
    abs(low_i - pre_close_i)
)
```

然后：

```text
atr_14 = mean(TR_{t-13}, ..., TR_t)   （最近 14 个 TR）
```

单位：index points。本文档不在此解释 ATR 的"市场过热"等业务意义。

### 6.5 Realized volatility

使用 close-to-close log return：

```text
r_i = ln(close_i / close_{i-1})
```

最近 N 个 return 的 realized volatility：

```text
RV_N = sample_std(r_{t-N+1}, ..., r_t) * sqrt(252) * 100
```

其中 `sample_std` 使用 **sample standard deviation（ddof = 1）**，`N` 表示 return 个数。

| 字段 | N | 公式 | 单位 |
| --- | --- | --- | --- |
| `realized_vol_5d_annualized_pct` | 5 | `sample_std(最近 5 个 r) * sqrt(252) * 100` | percentage points annualized |
| `realized_vol_20d_annualized_pct` | 20 | `sample_std(最近 20 个 r) * sqrt(252) * 100` | percentage points annualized |

`N = 5` 需要 6 个 close，`N = 20` 需要 21 个 close；120 日窗口保证这些字段始终可计算（窗口不足 120 日已在前置检查失败）。

### 6.6 derived 输出形态

`derived` 为单层对象，键为上述字段名，值为对应标量。不要输出序列，不要为每个历史日重复计算这些派生指标（历史窗口只保留 Raw Fact，派生指标只在 `t` 处求值一次）。

## 7. MO option chain preparation

> 交叉引用：本节定义的是 CSI1000 5D analysis `snapshot.json` 内 `mo_options` 的 preparation，与独立的 MO Option Chain data product（`../mo_option_chain/ARCHITECTURE.md` 及其子 Guide `../mo_option_chain/data.md`、`../mo_option_chain/read-contract.md`）是两回事——后者是与本数据产品并列的 read model，不依赖本 `snapshot.json`。本节的 join / 字段 / 排序语义保持不变。

### 7.1 输入与 join

输入：

```text
mo_option_basic.json
mo_option_daily.json
underlying_close（目标日收盘价，见 5.3）
```

按 `ts_code` 做 **deterministic one-to-one join**。

失败条件（任一成立则 Analysis Preparation 失败）：

```text
basic 缺 daily（active contract 无目标日 daily fact）
daily 缺 basic（daily fact 的 ts_code 无对应 basic）
duplicate ts_code（basic 或 daily 内同一 ts_code 出现多行）
```

### 7.2 字段映射

Analysis Preparation 允许把 Source-friendly 字段变成 analysis-friendly 字段：

```text
option_type ← call_put      （Source 值原样保留，仅重命名）
strike      ← exercise_price
expiry_date ← maturity_date
```

`expiry_date` 直接等于 `maturity_date`。Raw 层已按 [Shared Source Capture authority](../../capture/ARCHITECTURE.md) 将 `maturity_date`、`list_date` 与 `delist_date` 统一落地为 `YYYY-MM-DD`，因此 Analysis Preparation 只做 analysis-friendly rename `maturity_date → expiry_date`，不再做额外的日期格式归一化。

其余行情字段（`open` / `high` / `low` / `close` / `settle` / `vol` / `amount` / `oi`）沿用 `mo_option_daily` 的 Source 字段名与语义。

### 7.3 每张期权输出字段

```text
ts_code
option_type
strike
expiry_date
days_to_expiry

open
high
low
close
settle
vol
amount
oi

strike_minus_spot_points
moneyness_pct
close_premium_pct_of_spot
```

字段分类（见第 12 节的三种状态）：

* Structural / required：`ts_code`、`option_type`、`strike`、`expiry_date`、`days_to_expiry`。缺失、`null` 或 malformed → 失败。
* Derived-required numeric：`close`。它进入 `close_premium_pct_of_spot = close / underlying_close * 100`，因此 `close` 缺失或 `null` → 失败，不得作为 pass-through null 输出。
* Nullable pass-through：`open`、`high`、`low`、`settle`、`vol`、`amount`、`oi`。Source 合法缺失 / `null` → Analysis-ready Artifact 输出 `null`；present 但 malformed → 失败。

其中派生字段：

| 字段 | 公式 | 单位 |
| --- | --- | --- |
| `days_to_expiry` | `expiry_date - target_trade_date` | calendar days（整数） |
| `strike_minus_spot_points` | `strike - underlying_close` | index points |
| `moneyness_pct` | `(strike / underlying_close - 1) * 100` | percentage points |
| `close_premium_pct_of_spot` | `close / underlying_close * 100` | %（价格归一化） |

语义约束：

* `moneyness_pct` 只表达 strike 相对 spot 的位置，**不**根据 Call / Put 改变正负。
* `close_premium_pct_of_spot` 只做价格归一化，不表达"便宜/贵"。
* 这些字段不构成 ATM / OTM / ITM 分类，不构成交易建议。

### 7.4 排序

option chain 按以下 key 升序排列，使外部分析器可以直接读取完整价格面：

```text
expiry_date
strike
option_type
```

### 7.5 第一版明确不加

```text
ATM / OTM / ITM classification
cheap / expensive
IV
Delta / Gamma / Theta / Vega
probability
recommended strike
```

全部 deferred。

## 8. IM futures preparation

### 8.1 输入与 join

输入：

```text
im_futures_basic.json
im_futures_daily.json
underlying.history（供 60 日窗口与 underlying_close 使用）
```

以 `ts_code` 将 contract metadata（`im_futures_basic`）与 daily facts（`im_futures_daily`）做 deterministic join。`im_futures_daily` 中的每条 daily fact 必须能映射到 `im_futures_basic` 中的已知 IM 合约（取到 `delist_date`），否则 Analysis Preparation 失败。

### 8.2 60 日分析窗口

IM history 使用：

```text
underlying.history 中最后 60 个 trade_date
```

作为统一的 60 日分析窗口，使 CSI1000 spot 与 IM 的时间窗口天然对齐。**不另建交易日历**。

保留在这些日期中存在的 IM 普通月度合约 daily facts（合约限定来自 Raw Artifact 本身，见 `data.md` 5.2，不在 Preparation 层再做"主力/流动性"判断）。

`underlying.history` 含 120 个交易日，因此 60 日窗口内每个 IM 观测的 `trade_date` 都能在 `underlying.history` 中找到对应 close。

### 8.3 每条 futures observation 输出字段

```text
ts_code
trade_date
delist_date
days_to_delist

open
high
low
close
settle
vol
amount
oi
oi_chg

underlying_close
basis_points
basis_pct
annualized_basis_pct
```

其中 `underlying_close` 是该观测 `trade_date` 对应的 CSI1000 close（从 `underlying.history` 按 `trade_date` 对齐），其余行情字段沿用 `im_futures_daily` 的 Source 字段名与语义。

字段分类（见第 12 节的三种状态）：

* Structural / required：`ts_code`、`trade_date`、`delist_date`、`days_to_delist`。
* Derived-required numeric：`close`、`underlying_close`。其中 `underlying_close` 来自 underlying history；`close` 进入 `basis_points` / `basis_pct` / `annualized_basis_pct`，因此 `close` 缺失或 `null` → 失败。
* Nullable pass-through：`open`、`high`、`low`、`settle`、`vol`、`amount`、`oi`、`oi_chg`。Source 合法 null → Analysis-ready Artifact null；例如 `oi_chg == null` 表达首个可观察交易日 Source 没有该变化事实。

#### Raw → Analysis-ready Artifact projection

`im_futures_daily` Raw Artifact 可以包含更多 Source facts，例如 `pre_close`、`pre_settle`、`change1`、`change2`（见 [Shared Source Capture authority](../../capture/ARCHITECTURE.md)），但第一版 Analysis-ready Artifact 只选择 §8.3 明确列出的字段。

因此：

```text
Raw contains field
≠
Analysis-ready Artifact must contain field
```

Analysis-ready Artifact 是 deterministic analysis-ready projection，不是 Raw 的完整复制。`pre_close`、`pre_settle`、`change1`、`change2` 第一版不进入 IM analysis-ready observation（`history` 与 `target_date_curve` 都不包含）；这不是 data loss bug 或 schema drift，而是 Analysis Preparation Definition 的显式 projection。不要把这些字段加入 implementation。

### 8.4 派生字段

| 字段 | 公式 | 单位 |
| --- | --- | --- |
| `days_to_delist` | `delist_date - trade_date` | calendar days（整数） |
| `basis_points` | `futures_close - underlying_close` | index points |
| `basis_pct` | `(futures_close / underlying_close - 1) * 100` | percentage points |
| `annualized_basis_pct` | `days_to_delist > 0`：`basis_pct * 365 / days_to_delist`；`days_to_delist == 0`：`null` | percentage points annualized |

观测只存在于合约上市至退市的区间内，故 `days_to_delist >= 0`。这是简单线性年化。**不要**把它解释成看多 / 看空、贴水值得交易、滚仓信号等。

### 8.5 排序

IM `history` 按以下 key 升序排列（确定性顺序）：

```text
trade_date
ts_code
```

（`ts_code` 在同一 `trade_date` 内唯一，故该顺序是确定的；按到期日组织的便捷视图见第 9 节。）

## 9. IM target-date curve

为了让 analyzer 不需要从 60 日历史中再次寻找当前期限结构，Analysis-ready Artifact 同时提供 deterministic convenience view：

```text
im_futures.target_date_curve
```

定义：

```text
history 中 trade_date == target_trade_date 的投影
```

按：

```text
delist_date ascending
```

排序。字段沿用第 8.3 节。

它不是新的 Source Fact，也不是新的 Source Capture，只是 Analysis-ready Artifact 内对已有 deterministic facts 的重新组织。

## 10. 推荐 JSON 结构（结构 authority）

本节是结构 authority；示例数值只允许作为明显的 placeholder，不形成任何业务结论。

```json
{
  "target_trade_date": "2026-09-17",

  "underlying": {
    "ts_code": "000852.SH",
    "history": [
      {
        "trade_date": "2026-04-02",
        "open": 0,
        "high": 0,
        "low": 0,
        "close": 0,
        "pre_close": 0,
        "change": 0,
        "pct_chg": 0,
        "vol": 0,
        "amount": 0
      }
    ],
    "derived": {
      "return_1d_pct": 0,
      "return_5d_pct": 0,
      "return_20d_pct": 0,
      "sma_5": 0,
      "sma_20": 0,
      "sma_60": 0,
      "rolling_high_20": 0,
      "rolling_low_20": 0,
      "atr_14": 0,
      "realized_vol_5d_annualized_pct": 0,
      "realized_vol_20d_annualized_pct": 0
    }
  },

  "mo_options": {
    "underlying_close": 0,
    "chain": [
      {
        "ts_code": "MO2609-C-7600.CFE",
        "option_type": "C",
        "strike": 0,
        "expiry_date": "2026-09-17",
        "days_to_expiry": 0,
        "open": 0,
        "high": 0,
        "low": 0,
        "close": 0,
        "settle": 0,
        "vol": 0,
        "amount": 0,
        "oi": 0,
        "strike_minus_spot_points": 0,
        "moneyness_pct": 0,
        "close_premium_pct_of_spot": 0
      }
    ]
  },

  "im_futures": {
    "history": [
      {
        "ts_code": "IM2609.CFE",
        "trade_date": "2026-06-19",
        "delist_date": "2026-09-18",
        "days_to_delist": 0,
        "open": 0,
        "high": 0,
        "low": 0,
        "close": 0,
        "settle": 0,
        "vol": 0,
        "amount": 0,
        "oi": 0,
        "oi_chg": 0,
        "underlying_close": 0,
        "basis_points": 0,
        "basis_pct": 0,
        "annualized_basis_pct": 0
      }
    ],
    "target_date_curve": []
  }
}
```

说明：

* `underlying.history` 恰好 120 行；上面只示意 1 行。
* `underlying.derived` 为单层标量对象。
* `mo_options.chain` 按 `expiry_date, strike, option_type` 升序；`mo_options.underlying_close` 等于 `underlying.history` 末行 close。
* `im_futures.history` 只含第 8.2 节 60 日窗口内的观测，按 `trade_date, ts_code` 升序；`target_date_curve` 是 `trade_date == target_trade_date` 的投影，按 `delist_date` 升序。

## 11. Reproducibility

Analysis Preparation 必须只依赖第 3.1 节列出的输入。

不得：

```text
调用 Tushare
访问网络
使用当前时间
使用随机数
自动 fallback
读取其他日期目录补数据
```

同一组 Raw + 同一 Definition 必须产生语义一致的 Analysis-ready Artifact（结构一致、字段一致、数值一致）。

Analysis-ready Artifact 内不得出现无法回溯到 Raw Artifact 的"只存在于 Analysis-ready Artifact 中的数据事实"。所有派生字段都可按本文档公式从 Raw 确定性重算。

## 12. Completeness failure

Analysis Preparation 不得静默估算或跳过关键记录。先明确 numeric fact 的三种状态，再锁定失败条件。

### A. Required structural / derived input

字段用于 identity、join、window selection、date calculation 或 derived formula 时：

```text
missing
null
malformed
NaN
infinity
```

全部 → Analysis Preparation fail。不得填零、估算或 fallback。

### B. Nullable Source pass-through fact

字段只作为 Source fact 被复制到 Analysis-ready Artifact，且不参与任何 required derived formula 时，Source 合法未提供该事实：

```text
missing key
or
null
```

允许 → Analysis-ready Artifact 输出 `null`。这表示：

```text
Source 没有这个事实
```

不是 `0`，也不是未知值的估算。字段非 null 但 malformed（string、NaN、infinity、invalid numeric representation）仍然 → fail。

### C. Derived field explicitly defines null

`annualized_basis_pct` 在 `days_to_delist == 0` 时 authority 已定义为 `null`（第 8.4 节）。这是 derived semantic null，与 Source pass-through null 是不同原因；保持现有语义。

失败条件（任一成立则 Analysis Preparation 失败）：

```text
underlying < 120 days → fail

underlying target_trade_date missing → fail

MO basic/daily cannot one-to-one join → fail

IM daily cannot map to known IM contract → fail

required structural / derived input missing / null / malformed → fail

nullable pass-through fact present but malformed → fail
```

补充：MO chain 为空、IM history 为空（进而 `target_date_curve` 为空）也属于 Raw 不完整，失败而非静默输出空结果。本文档不设计复杂 validation framework，简单明确即可；具体异常类型、CLI exit code 属于 implementation，可 deferred。

## 13. Deferred（第一版明确不做）

```text
option IV
Greeks
ATM-straddle implied move
volatility skew summary
option surface interpolation

futures pairwise calendar-spread summary

breadth
stock_daily
macro
news
fund flow

analysis prompt
business conclusion schema
```

以后有明确数据需求时再增加，不在本 Goal 顺手加入。

## 14. 与第一版 daily-market-snapshot 场景的关系

* 现有 `../daily_market_snapshot/ARCHITECTURE.md` 及其 `data/snapshots/YYYY-MM-DD/snapshot.json` 继续独立存在，不被本 Guide 破坏或重定义。
* CSI1000 场景使用独立的 `output/csi1000-5d-analysis/YYYY-MM-DD/snapshot.json`（Data Service canonical output，见 [delivery authority](../../services/delivery.md)），与第一版 daily-market-snapshot 场景的 Raw 目录、输出目录互不冲突。
* `000852.SH` 同时出现在两个场景中，但语义不同：第一版 daily-market-snapshot 场景中它是六指数观察 universe 的成员；本场景中它是 `underlying` 的标的。两者复用同一 `index_daily` Source Capture 语义，不复制新 Capture。

## 15. 实现约束

实现必须读取 [data.md](data.md) 定义的五个 Raw Artifacts，并严格按本文档的窗口、join、公式、排序、null 与失败条件产出 `output/csi1000-5d-analysis/<target_trade_date>/snapshot.json`。实现不得发明业务语义；与本文档不一致时必须显式 reconciliation。
