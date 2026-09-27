# IM Basis Preparation Semantics authority

本文档是 `market-snapshot` 内 IM 期限位置、剩余日历天数与 CSI1000 基差计算的唯一 canonical semantic owner。Product ownership 与 execution roles 见 [market-snapshot architecture](../../../../ARCHITECTURE.md)；Source 字段事实见 [IM futures Source contract](../../capture/im-futures-contract.md)。

本 context 的既有 IM basis 语义仍由 CSI1000 IM Basis History 消费，并保持该产品依赖的 canonical owner。它只提供窄义 deterministic Preparation semantics，不是全局 Preparation ownership layer、通用 feature framework、Preparation engine 或 Research interface。产品自己的 query、Source scope、Source Facts / Raw Artifact、result shape、completeness 和 delivery 继续由产品 authority 拥有。

## 1. Required facts

对每个 observation trade date，本语义使用：

```text
trade_date

IM contract identity
IM list_date
IM delist_date / maturity fact
IM futures_close

CSI1000 (000852.SH) same-trade-date underlying_close
```

`trade_date`、`list_date`、`delist_date`、合约身份、合约月份与两个 close 都是 required input。缺失、`null`、malformed、非有限 numeric value，或 `underlying_close == 0`，均不得通过填零、换日期或猜测修复。

## 2. Active IM universe

一个普通月度 CFFEX IM 合约在交易日 `T` 属于 active universe，当且仅当：

```text
list_date <= T <= delist_date
```

每个 `T` 保留全部 active IM contracts。不得根据以下事实或解释性条件筛选：

```text
volume
open interest
main-contract designation
liquidity threshold
research preference
```

`volume` 和 `oi` 可以被产品作为 Source diagnostic fact 保留，但不参与 universe 或 slot 判定。

## 3. Contract month and slot

`contract_month` 是合约的年-月 maturity fact。V1 从 `delist_date` 所在年-月确定，并要求它与合约 identity 所表达的月份一致；两者无法一致验证时失败，不得选择其中一个猜测。

对每个 `trade_date` 独立执行：

1. 取第 2 节定义的全部 active contracts。
2. 要求每个 `contract_month` 只有一个合约，共恰好四个不同月份。
3. 按 `contract_month` ascending 排序：前两个月份必须连续，依次映射为 `M0`、`M1`。
4. 后两个月份必须是严格晚于 `M1` 的前两个季月（3、6、9、12 月），依次映射为 `Q1`、`Q2`。

`contract_slot` 表达当日 term-structure position，不是固定 DTE bucket。`M0` 是当日最前端的有效月度位置；前月合约交割后，下一个有效月份自然成为 `M0`。`contract_slot` 与 `days_to_delist` 必须同时保留，不得相互代替。

合约数量不是四个、月份重复、前两月不连续、季月序列不符合约定或必需事实不足以唯一映射时，均为显式 data-quality failure。不得使用 volume、OI、主力标记或研究偏好打破并列。

## 4. Calendar distance and annualization

Calendar fact：

```text
days_to_delist = delist_date - trade_date
```

单位为 calendar days（整数）。Active observation 要求 `days_to_delist >= 0`；在 delist / delivery date：

```text
days_to_delist = 0
```

为年化计算定义独立 denominator：

```text
annualization_days = max(days_to_delist, 1)
```

因此交割日是 `days_to_delist = 0` 且 `annualization_days = 1`。不得为避免除零而篡改 calendar fact。

## 5. Basis formulas

`underlying_close` 固定为 CSI1000（`000852.SH`）同一 `trade_date` 的 close，`futures_close` 为该 IM 合约同日 close。Canonical formulas 为：

```text
basis_points
= futures_close - underlying_close

basis_pct
= (futures_close / underlying_close - 1) * 100

annualized_basis_pct
= basis_pct * 365 / annualization_days
```

Units：

| Field | Unit |
| --- | --- |
| `basis_points` | index points |
| `basis_pct` | percentage points |
| `annualized_basis_pct` | percentage points annualized |

V1 使用 simple linear annualization，不定义 log 或 continuously compounded basis yield。这些字段只是 deterministic market facts，不表达 bullish/bearish、贵/便宜、交易信号、套利规则或推荐。

## 6. Canonical observation order

使用本语义的 flat observation panel 默认按以下 key ascending：

```text
trade_date
contract_slot order: M0, M1, Q1, Q2
ts_code
```

`ts_code` 是稳定 tie-breaker，不参与 slot 判定。

## 7. Consumers and maintenance

当前 consumer：[CSI1000 IM Basis History](../../products/csi1000_im_basis_history/ARCHITECTURE.md)。

该 Product 引用本 authority，不复制公式或创建产品私有的 slot 定义。只有 IM slot、calendar distance 或 basis formula 本身改变时才修改本文档；产品 query、result 或 Research method 变更应进入其各自 authority。
