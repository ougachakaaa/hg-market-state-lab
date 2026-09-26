# MO Option Chain HTTP transport contract authority

本文档从属于 [backend-api HTTP product catalog](../../HTTP_PRODUCTS.md)，只拥有 endpoint、method、query serialization、response projection、error envelope 与 HTTP status mapping。它不重新定义 market semantics：

```text
query identity / product / underlying / invariants       → market-snapshot product authority
Source / Raw / universe / completeness                  → market-snapshot data authority
price / null / grouping / ordering / response / failure → market-snapshot read contract
HTTP transport                                           → 本文档
```

本文档只把 [market-snapshot read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 的 semantic failure categories 映射为 transport，不改变 category 本身。

Markdown authority 拥有 market / read semantics 与本 Guide 的 HTTP transport 语义。后端 Pydantic HTTP DTO 及其发布的 OpenAPI 是 HTTP wire contract 的可执行表达，必须忠实反映这些 authority；OpenAPI 是前端获取机器可读 wire shape 的来源。`web-ui` 消费该契约，不另行人工定义一套与其平行的 backend market / transport schema。仓库验证必须在后端 OpenAPI 与前端消费的契约产物不同步时失败。

---

## 1. Endpoint

```text
GET /mo-option-chain
```

* V1 只定义这一个 MO Option Chain read surface。
* 读操作使用 GET，没有 request body，也不修改客户端可操作的业务资源。Data Service 在读取 Source 时会按 [data authority](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/data.md) 写入 goal-scoped Raw Artifact；这属于数据准备流程，不改变 HTTP read contract。
* query identity 的三个维度全部通过 query 参数表达（第 2 节）。
* 路径中不带 date / product：这些是 query identity，不是资源层级。
* 本阶段不引入 API version 前缀、不提供写操作、不提供第二个 endpoint（见第 8 节）。

示例：

```text
GET /mo-option-chain?target_trade_date=2026-09-17&option_product=MO
GET /mo-option-chain?target_trade_date=2026-09-17&option_product=MO&price_type=high
```

## 2. Request / Query Parameters

| 参数 | required | 类型 | 语义 |
| --- | --- | --- | --- |
| `target_trade_date` | required | string | 显式 target trade date，格式 `YYYY-MM-DD`；不是 today / latest / current date |
| `option_product` | required | string | 期权产品；V1 唯一支持 `MO` |
| `price_type` | optional | string | 取价口径；缺省解析为 `close` |

规则：

* 语义 authority 是 [MO Option Chain product authority](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 第 3 节；本节只规定它们在 HTTP 上的表达形式。
* `price_type` 省略时由服务端按 authority 固定默认 `close` 解析（不要求 caller 显式给出）。
* `price_type` 的可用取值是 `open` / `high` / `low` / `close`（[read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 第 1 节）；`settle` / `pre_close` / `pre_settle` / `volume` 不接受。
* HTTP 层不接受也没有 underlying 参数：`MO → 000852.SH` 的映射由 data product 拥有，caller 不得同时指定两个可能矛盾的输入（[product authority](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 第 4 节）。
* HTTP 层不接受任何额外查询参数，也没有 `latest` / `date range` / 自动 fallback 形态。
* HTTP 层不定义“最近交易日”查询、availability 查询或任何日期推断：`target_trade_date` 必须由 caller 显式给出。

## 3. Success Response

HTTP 200，body 为单个 JSON object，形状与 [read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 第 8 节的 semantic response 完全一致；HTTP 层不包裹 envelope、不改名、不增删字段。

当某到期日无结构性匹配的 IM 合约时，该到期日仍在成功响应中，且显式包含 `"futures": null`；有唯一匹配时则为下面示例中的 object。

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

transport 必须保持的语义（全部由 read contract 拥有，本文档只声明 HTTP 序列化不得破坏它们）：

* `expiries` 一级按 `expiry_date` ascending，二级 `calls[]` / `puts[]`，三级 `strike` ascending，同 strike 以 `instrument_id` ascending 作稳定 tie-break（read contract 第 6、7 节）。
* option point 只有 `instrument_id` / `strike` / `price` 三个字段：`expiry` 由父级 `expiries[]` 表达，`option_type` 由 `calls[]` / `puts[]` 归属表达，point 上不重复携带。
* option point 的 `price` 允许 `null`，且必须序列化为 `null`：不得用 `exclude_none` 之类的方式省略该字段、不得补 `0`、不得删除 contract（read contract 第 3 节）。
* numeric `0` 是合法 fact，必须原样返回 `0`，不得写成 `null`。
* `underlying.price` 必须是 usable numeric fact；成功 response 不允许 underlying price 为 `null`（read contract 第 4 节）。
* 每个 `expiries[]` 项必须包含 `futures` 字段；无结构性匹配时为 `null`，唯一匹配时为包含非 `null` `instrument_id` 与 usable numeric `price` 的 object。HTTP 层原样序列化 read model，不执行匹配、选价或格式化（read contract 第 4 节）。
* response 是 self-describing 的：`target_trade_date`、`option_product`、resolved `price_type`、`underlying.instrument_id` 与每个 expiry 的 `futures` 字段必须出现在 body 中，客户端不依赖自己的 local state 才能解释 response（read contract 第 9 节）。`price_type` 回显的是 **resolved** 值（caller 省略时即 `close`），不是省略态。
* 即使全部 contract 的 `price` 都是 `null`，只要结构完整，仍是 200 success（read contract 第 10 节）。

## 4. Error Response

非 2xx 时 body 为**单一** error envelope：

```json
{
  "error": {
    "kind": "date_not_available",
    "detail": "target_trade_date 2026-09-17 is not a trading date with MO option-chain data",
    "param": "target_trade_date"
  }
}
```

字段：

| 字段 | required | 含义 |
| --- | --- | --- |
| `error.kind` | required | 闭集 error kind（见第 5 节）；客户端据它分支，不解析 `detail` 文本 |
| `error.detail` | required | 人类可读说明；非稳定 contract，不得作为程序判断依据 |
| `error.param` | optional | 导致失败的 query 参数名；仅当失败可归因到某个 caller 参数时出现 |

约束：

* error kind 是**闭集**：V1 只允许第 5 节列出的取值。
* envelope 只表达 transport 结果，不携带任何 market fact；不得用 error response 返回 partial chain、替代日期或补齐数据（read contract 第 12 节 no-silent-recovery）。
* error response 不得包含 underlying price、contract、expiry 等任何 chain 内容。

## 5. Error Kind → HTTP Status Mapping

mapping 的输入是 [read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 第 11 节的 semantic failure categories。HTTP 层只做映射，不新增、不合并、不重新解释这些 category：

| error kind | HTTP status | semantic failure category（read-contract 第 11 节） |
| --- | --- | --- |
| `invalid_request` | 400 | `invalid target_trade_date format`；以及 transport 层面拒绝的 request（缺 required 参数、参数取值不在契约允许集合内、携带契约未声明参数） |
| `unsupported_query` | 400 | `unsupported option_product`；`unsupported price_type` |
| `date_not_available` | 404 | `target_trade_date cannot be served by Source`；`non-trading / unavailable date` |
| `option_chain_unavailable` | 503 | `cannot determine product → underlying`；`cannot determine active contract universe`；`active contract missing target-date daily row`；`duplicate / inconsistent contract identity`；`required structural field missing or malformed`；`underlying selected price unavailable or malformed`；expiry 有多个 IM 普通月合约匹配，或唯一匹配后 IM 目标日 daily row 缺失或重复、所选 IM price 缺失或 malformed |
| `service_not_wired` | 503 | 非 semantic failure：delivery adapter 没有 provider binding；仅保留用于 bootstrap/test compatibility |

**谁产生 `invalid_request`，谁产生 `unsupported_query`：**

* `invalid_request` 由 HTTP 层产生。HTTP 层的输入闭集是 `target_trade_date` / `option_product=MO` / `price_type∈{open,high,low,close}`：任何落在闭集之外的请求（缺参数、`option_product` 非 `MO`、`price_type` 取值不合法、未知参数）都是 transport 拒绝。
* `unsupported_query` 来自 read model：只有当 Data Service / Preparation 明确报告“该 query 形态合法但 V1 不支持”时（例如将来 Source 侧不支持的 `price_type` / `option_product`）才使用。只读 HTTP 层不自行发明该 kind。
* 两者都是 400：重试同一个 request 不会成功。

理由：

* `400`：request 本身不合法或要求了 V1 明确不支持的能力，重试同样的 request 不会成功。
* `404`：query identity 明确、产品受支持，但该 `target_trade_date` 在 authority 下不可服务（非交易日 / 数据尚未发布 / Source 无该日数据）。不使用 3xx 或 fallback：no-silent-recovery 要求显式失败。
* `503`：语义上的“当前无法提供完整 chain”属于服务端暂时无法满足一个合法请求（数据不完整、Source fact 缺失、underlying 或唯一匹配的 IM futures reference 不可用）。无匹配 IM 的 `futures = null` 是完整的成功 chain；实际数据缺失不得降级成 200 + partial chain。

其他真实 HTTP 结果（不属于上述 business mapping，由 HTTP 语义本身决定）：

```text
unknown path / endpoint        → 404
unsupported HTTP method        → 405
非 JSON 的不可恢复服务端缺陷    → 500
```

`invalid_request` 的具体判定：

* `target_trade_date` 不满足 `YYYY-MM-DD` → `invalid_request`，`param = "target_trade_date"`。
* 缺少 `target_trade_date` 或 `option_product` → `invalid_request`，`param` 为缺失参数名。
* `option_product` 不是 `MO`，或 `price_type` 不在 `{open, high, low, close}` 内 → `invalid_request`，`param` 为对应参数名。
* 携带契约未声明的 query 参数 → `invalid_request`；该参数不属于契约字段，因此 `param` 为 `null`，由 `error.detail` 指出。

`error.param` 只填契约声明的参数名（`target_trade_date` / `option_product` / `price_type`），因此对未知参数与整个 chain 的失败（`option_chain_unavailable` / `service_not_wired`）都为 `null`。

## 6. Ownership

HTTP delivery 拥有（[backend-api architecture](../../ARCHITECTURE.md) 第 2 节）：

```text
transport
request serialization
response serialization
HTTP error representation
```

HTTP delivery **不**拥有，也不得在 DTO / router / status mapping 中重新定义：

```text
option product identity
option product → underlying mapping
contract universe / lifecycle
selected price semantics / fallback
per-expiry IM matching / futures selected price
null vs zero semantics
grouping / ordering
completeness（daily row、structural field）
market semantics / analysis interpretation
```

具体实现约束：

* `price_type` 默认值 `close` 是 authority 的解析规则，不是 HTTP 层的自由选择；HTTP 层只回显 resolved 值。
* DTO 不得引入 authority 没有的字段（例如 moneyness、volume、open interest、IV、greeks、liquidity 标记），也不得在 point 上重复携带 `expiry_date` / `option_type`；`futures` 只属于父级 expiry group。
* DTO 不得把 `price` 收紧为 required numeric：`null` 是合法状态。
* router 不得做 product / underlying / universe / completeness 判断；这些是 Data Service / Preparation 的职责。HTTP 层只做 transport 级校验（参数形态、V1 支持范围）与 envelope 映射。

## 7. Delivery Boundary & Data Source

```text
MO Option Chain read model（market-snapshot 拥有语义）
        ↓
Data Service / application boundary（返回 read model 或抛出失败）
        ↓
HTTP delivery adapter（本文档：DTO + envelope + status）
        ↓
web-ui
```

* HTTP 层通过明确的 service/application boundary 获取 read model；它不读 Raw Artifact，不调用 Source，不理解 Tushare。
* HTTP 层不依赖 `csi1000-5d-analysis` 的 `snapshot.json`（见 [product authority](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) Stable Product Invariant 1）。
* HTTP contract tests 可以注入 fake service 验证 transport；fake 不属于业务语义层，也不得定义 market semantics。
* local 启动默认 bind `127.0.0.1:8011`（launcher 细节，可用 `--host` / `--port` 覆盖）。端口号**不属于**本 contract：endpoint 语义始终是 `GET /mo-option-chain`，换端口不改变 request / response / error 契约；V1 不定义 deployment、反向代理、TLS 或 CORS（见第 8 节）。

## 8. V1 Non-goals

本阶段 HTTP 层不做：

```text
API version 前缀 / versioning 策略
auth / token / session
CORS policy
pagination / filtering / sorting 参数
response envelope / metadata wrapper
第二个 endpoint（availability / latest / date-range）
写操作
websocket / streaming
cache / ETag 语义
OpenAPI client 生成
server deployment / 反向代理 / TLS 配置
```

`service_not_wired` 仅保留作 bootstrap/test compatibility；它不属于 market semantic failure。

## 9. 完成自检

仅阅读本文档与 [product authority](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) / [read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md)，应能唯一回答：

1. endpoint URL 与 method 是什么？
2. 哪些 query 参数是 required，默认值是什么？
3. 成功 response 的 JSON 形状是什么？哪些字段必须出现？
4. option point 的 `price` 何时是 `null`，何时是 `0`？
5. 失败 response 的 envelope 是什么？`kind` 的闭集有哪些？
6. 每个 semantic failure category 映射到哪个 HTTP status？
7. 为什么 `invalid_request` / `unsupported_query` / `date_not_available` 是不同 status？
8. HTTP 层明确不拥有哪些语义？
9. 为什么不能 `exclude_none`、不能补 `0`、不能删除 contract？
10. HTTP 层从哪里获得 read model，为什么它不知道 Tushare / Raw？
