# MO Option Chain read contract authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 selected price、null/zero、grouping、ordering、semantic response shape、success/failure 与 no-silent-recovery。Source、Raw、universe 与 completeness 见 [data.md](data.md)；HTTP transport 见 [backend-api contract](../../../../../backend-api/products/mo_option_chain/http-contract.md)。

---

## 1. price_type

V1 支持：

```text
open
high
low
close
```

默认：

```text
close
```

（caller 省略 `price_type` 时的 authority 默认，见 `ARCHITECTURE.md` 第 3 节。）

`volume` 不属于 `price_type`，因为：

```text
volume is not a price
```

V1 也不支持：

```text
settle
pre_close
pre_settle
```

这些以后有明确需求时再增加。尤其 `settle` 暂不进入 V1，因为 underlying index 没有与期权 settlement 完全对称的统一 reference semantic。

## 2. Unified Price Semantics

同一次 query 中：

```text
options
AND
underlying
AND
each present expiry IM futures reference
```

必须使用相同的：

```text
price_type
```

例如 `price_type = close`：

```text
option.price     ← option close
underlying.price ← CSI1000 close
expiry.futures.price ← matching IM close
```

`price_type = high`：

```text
option.price     ← option high
underlying.price ← CSI1000 high
expiry.futures.price ← matching IM high
```

不得产生：

```text
option high + underlying close
option close + underlying close + futures settle
```

这种混合语义。因此整个 response 表示的是：

> 目标交易日在同一种 daily price semantics 下的 option chain、underlying reference 与实际存在的各到期日 IM futures reference。

## 3. Selected Price Null Semantics

必须区分：

```text
0
```

和：

```text
null
```

### Numeric zero

如果 Source 返回：

```text
0
```

这是一个合法 numeric fact，必须原样返回：

```text
price = 0
```

不得解释为 missing。

### Null / missing selected field

如果 active contract：

```text
daily row exists
```

但选定的 `price_type` 对应字段没有 Source fact：

```text
null
or
missing
```

则：

```text
price = null
```

contract 仍然保留在 response 中。

不得：

```text
fill zero
fallback to close
fallback to settle
fallback to previous date
drop contract
```

因此：

```text
Contract Completeness ≠ Selected Price Availability
```

一个 contract 可以：

```text
exist in complete chain
AND
price = null
```

## 4. Required Reference Prices

### Underlying price

与 option contract 不同，underlying 是整个 visualization 的共享 reference。

因此成功 response 要求：

```text
underlying selected price
```

必须存在且是 usable numeric fact。

如果目标日期的 underlying `price_type`：

```text
不存在
或 malformed
```

则：

```text
request fails
```

不得返回一个没有有效 underlying reference 的 successful chain。

### Per-expiry IM futures reference

Preparation 先从 `data.md` 第 8 节定义的 **target-date-active IM ordinary monthly universe** 建立候选集，再对每个 MO `expiry_date` 应用 Source 结构性事实匹配：

```text
candidates = target-date-active IM ordinary monthly contracts
             where IM.delist_date == MO.expiry_date
len(candidates) == 0 → futures = null，chain 仍成功
len(candidates) == 1 → futures 为匹配合约及其目标日价格
len(candidates) > 1 → 整个 chain 失败
```

生命周期不覆盖 `target_trade_date` 的 IM 合约即使 `delist_date` 相同，也不能成为候选。不得解析 `MO2609` / `IM2609` 字符串、按月份猜测、选主力合约或按流动性选择。IM 是该 expiry 的 futures reference，不是 MO 的 underlying；`MO → CSI1000 → 000852.SH` 映射不变。

唯一匹配合约的 `instrument_id` 来自其 Source `ts_code`；`futures.price` 来自该合约唯一目标交易日 `fut_daily` row 的 resolved `price_type` 字段。该 row 与价格必须存在，价格须为 usable numeric fact，数值 `0` 是合法事实；不能为 `null`、用其他价格字段或其他月份替代。

无匹配合约是有效市场结构，须显式返回 `futures = null`，不得推断替代合约。多个匹配合约，或唯一匹配后的目标日 daily row 缺失或重复、所选价格缺失或 malformed，均使整个 chain 失败。

这里的 daily row / selected price 完整性只针对各 expiry **实际匹配**的 IM 合约。IM Raw 采集覆盖所有目标日有效普通月合约；未匹配任何 MO expiry 的合约缺 daily row 不自动使 MO Chain 失败，也不得因此改选匹配合约。Source 请求错误仍按 data contract 显式失败。

## 5. Contract Business Identity

每个 option contract 必须携带稳定业务 identity。

read contract 使用：

```text
instrument_id
```

表达这一概念。

V1 可以直接使用现有 Source `ts_code` 的值，例如：

```text
MO2609-C-7000.CFE
```

但 read contract 的业务语义是：

```text
stable option instrument identity
```

而不是：

```text
frontend must understand Tushare ts_code semantics
```

因此未来即使 Source 改变，也不需要修改 read contract 中 identity 这一业务概念。

underlying 的 identity 同样使用：

```text
instrument_id = "000852.SH"
```

## 6. Grouping

response 不返回需要 React 自行解释的 flat chain。

Preparation 必须完成 deterministic organization。

一级：

```text
group by expiry
```

二级：

```text
group by option type
```

逻辑结构：

```text
expiries[]
    expiry_date

    futures = null | {
        instrument_id
        price
    }

    calls[]
    puts[]
```

Call / Put grouping 属于数据 contract，不属于 React 的业务判断；`option_type` 由 `calls[]` / `puts[]` 的数组归属表达，不要求在 point 上重复携带 `option_type` 字段。`expiry_date` 由 `expiries[]` 的父级表达，不要求在 point 上重复。

## 7. Ordering

deterministic ordering 属于 contract。

```text
expiry_date ascending
    ↓
option_type grouping（calls[] / puts[]）
    ↓
strike ascending
    ↓
instrument_id ascending（同 strike 的稳定 tie-break）
```

React 不需要自行决定业务顺序。

## 8. Read Contract（semantic shape）

推荐 V1 semantic response：

```json
{
  "target_trade_date": "2026-09-17",
  "option_product": "MO",
  "price_type": "close",

  "underlying": {
    "instrument_id": "000852.SH",
    "price": 7312.45
  },

  "expiries": [
    {
      "expiry_date": "2026-09-25",

      "futures": {
        "instrument_id": "IM2609.CFE",
        "price": 7487.6
      },

      "calls": [
        {
          "instrument_id": "MO2609-C-7000.CFE",
          "strike": 7000.0,
          "price": 356.4
        },
        {
          "instrument_id": "MO2609-C-7200.CFE",
          "strike": 7200.0,
          "price": null
        }
      ],

      "puts": [
        {
          "instrument_id": "MO2609-P-7000.CFE",
          "strike": 7000.0,
          "price": 41.8
        }
      ]
    }
  ]
}
```

这是 semantic authority。

不是：

```text
Pydantic definition
HTTP schema implementation
OpenAPI definition
```

这些属于 delivery 层，由 [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md) 拥有；read contract 只锁 semantic shape，不锁其 transport 表达。

字段到 Source 的确定性投影（Preparation 职责，非 web-ui 职责）：

```text
instrument_id    ← Source ts_code
strike           ← Source exercise_price（numeric）
expiry_date      ← Source maturity_date（已归一化为 YYYY-MM-DD）
price            ← Source opt_daily 的 price_type 字段
underlying.price ← Source index_daily（000852.SH）的 price_type 字段
futures         ← 无匹配 IM 普通月合约时为 null
futures.instrument_id ← 唯一匹配时该 IM 普通月合约 ts_code
futures.price   ← 唯一匹配时该 IM 合约目标日 fut_daily 的 price_type 字段
```

`call_put → calls[] / puts[]` 的归属是 Preparation 的确定性组织，`web-ui` 不参与该判断。

## 9. Self-describing Response

任何成功 response 单独存在时，都必须可以回答：

```text
哪一天？
哪个期权产品？
使用什么价格？
underlying 是谁？
有哪些 expiry？
有哪些 contracts？
```

因此必须返回：

```text
target_trade_date
option_product
price_type（resolved）
underlying identity
每个 expiry 的 futures 字段；有匹配时包含 IM identity 与目标日价格，无匹配时为 null
```

不得依赖 React 的 local state 才知道这些信息。

## 10. Success Semantics

成功表示：

```text
query identity is valid
+
underlying target-date fact exists
+
active option universe can be determined
+
every expiry has at most one matching target-date-active IM ordinary monthly contract; zero is valid absence
+
every matched IM contract has a usable target-date selected price
+
every active MO option contract has its target-date daily row
+
structural contract facts are complete
```

selected option price：

```text
可以为 null
```

而不会破坏 chain completeness。

因此即使：

```text
some contracts
or even all contracts
have price = null
```

data product 仍然可以在结构上返回完整 chain。这表示：

```text
chain exists
selected price facts unavailable
```

而不是：

```text
contracts do not exist
```

## 11. Failure Semantics

下列 `active contract` 指 MO option active universe 中的合约；IM daily-row failure 只针对各 expiry 实际匹配的合约（见第 4 节）。

以下属于 failure：

```text
invalid target_trade_date format

target_trade_date cannot be served by Source
non-trading / unavailable date

unsupported option_product

unsupported price_type

cannot determine product → underlying

cannot determine active contract universe

active contract missing target-date daily row

duplicate / inconsistent contract identity

required structural field missing or malformed

underlying selected price unavailable or malformed

expiry has multiple matching target-date-active IM ordinary monthly contracts
matched IM target-date daily row missing or duplicate
matched IM selected price missing or malformed
```

本文档不定义：

```text
HTTP status code
error JSON shape
exception class
```

这里只锁 semantic categories。semantic category → transport 的映射由 [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md) 拥有；本文档不重复，也不被其改写。

## 12. No Silent Recovery

任何 failure 均不得通过以下方式隐藏：

```text
fallback date
nearest trade date
latest available date
previous close
settlement substitution
omission of the futures field or substitution of a missing reference
zero fill
contract dropping
partial chain
fabricated instrument
```
