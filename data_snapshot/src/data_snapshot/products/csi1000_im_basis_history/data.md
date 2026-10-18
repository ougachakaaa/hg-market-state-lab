# CSI1000 IM Basis History data authority

本文档从属于 [product authority](ARCHITECTURE.md)，拥有本产品的 Source requirements、query-scoped Capture scope、observation dates 与 Source completeness。Source endpoint 与公共字段事实由 [Shared Source Capture authority](../../capture/ARCHITECTURE.md) 拥有；IM slot 与 basis 语义由 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) 拥有。

## 1. Required Source capabilities

V1 只使用：

```text
index_daily        CSI1000 / 000852.SH
im_futures_basic   CFFEX IM ordinary monthly contracts
im_futures_daily   requested contracts' daily facts
```

不采集 MO options，也不因研究目的增加 stock、macro、news 或其他数据。

## 2. Inclusive range and observation dates

Capture 使用产品 query 的显式 inclusive calendar bounds。在该区间内，Source 成功返回的 `000852.SH` index daily `trade_date` 集合定义本次 result 的 observation dates。

```text
observation_dates
= distinct CSI1000 trade_date
  where start_trade_date <= trade_date <= end_trade_date
```

产品不引入独立交易日历，不把周末或休市日制造为 observation，也不把某个区间边界自动换成最近交易日。成功请求至少必须有一个 observation date。

每个 observation date 必须有且只有一条 `000852.SH` daily row，其 `close` 必须是 usable non-zero finite numeric fact。

## 3. IM contract and daily scope

`im_futures_basic` scope 要能确定所有与 query interval 相交的 IM 普通月度合约：

```text
list_date <= end_trade_date
AND
delist_date >= start_trade_date
```

这只是 Capture scope；每日 active universe 继续由 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) 按完整生命周期事实确定。

对每个与 query interval 相交的合约，`im_futures_daily` 采集区间裁切为：

```text
max(start_trade_date, list_date)
through
min(end_trade_date, delist_date)
```

Capture 不计算 slot、days-to-delist 或 basis，也不根据 volume/OI 决定是否请求某个 active contract。

## 4. Completeness

对每个 observation date：

1. 必须能从 basic facts 确定完整 active IM universe。
2. 每个 active contract 必须有且只有一条该日 daily row。
3. 每条 daily row 必须映射到唯一 known active contract。
4. 合约的生命周期、月份和 identity facts 必须自洽。

任一必需 Source request 失败，或上述 completeness 不成立，均不得通过丢弃合约、丢弃交易日、使用其他日期、填零或返回 partial data 隐藏。

## 5. Raw boundary

实现可以使用产品自己的 query-scoped Raw Artifacts，但不得读取 sibling product 的 Raw 或 final artifact。Raw 只保留 Source facts 与 minimal normalization；精确 join、每日 universe validation、slot、formula、projection 和 ordering 属于 Analysis Preparation。

V1 不承诺 Raw path、final persistence layout、database 或 cache。这些都不是 Research consumer boundary。
