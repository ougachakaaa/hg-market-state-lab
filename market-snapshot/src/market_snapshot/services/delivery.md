# Data Service / CLI / output authority

本文档定义 Data Service application boundary、用户级 CLI 与 canonical user-facing persisted output。模块分层见 [market-snapshot architecture](../../../ARCHITECTURE.md)，产品语义从 [Capability Catalog](../../../CAPABILITIES.md) 进入对应 canonical owner；HTTP inbound delivery 由 [backend-api](../../../../backend-api/ARCHITECTURE.md) 拥有。本文档不重复 Source、Raw、Preparation、产品公式或 HTTP transport。

## 1. 什么是 Data Service

Data Service 是用户可直接请求的完整数据能力。一个 Data Service 可以由多个 Source Capture、Raw Artifact 与 deterministic Analysis Preparation 共同生成。

关系：

```text
Data Service
    ↓
orchestrates existing Source Capture / Analysis Preparation
    ↓
declared result / delivery
```

Data Service 不是：

```text
Source Capture
Raw Artifact
Analysis Preparation
Source
Pipeline framework
Workflow engine
Plugin
```

它只是最上层的**用户调用语义单位**。每个 Data Service 拥有自己的 query identity 与 result semantics，由对应产品 authority 定义，并从 repository [Capability Catalog](../../../CAPABILITIES.md) 路由，不共用同一个 `service_id + target_trade_date` 模板。调用方不需要知道底层有哪些 Source Capture，只需要按该 service 自己定义的 query identity 指定输入。

## 2. Repository Data Service Semantic Catalog

Repository authority 声明以下五个用户可请求的 Data Service semantic identities，不为了丰富 catalog 创造其他服务：

| service_id | input | result / delivery | 产品 authority |
| --- | --- | --- | --- |
| `csi1000-5d-analysis` | `target_trade_date`（CLI 的 `--date`） | persisted `snapshot.json` | [product authority](../products/csi1000_5d_analysis/ARCHITECTURE.md) |
| `csi1000-im-basis-history` | `start_trade_date + end_trade_date` | request-scoped `CSI1000IMBasisHistoryResult` | [product authority](../products/csi1000_im_basis_history/ARCHITECTURE.md) |
| `index-daily-history` | `ts_code + start_trade_date + end_trade_date + pre_start_observation_count` | request-scoped `IndexDailyHistoryResult` | [product authority](../products/index_daily_history/ARCHITECTURE.md) |
| `mo-option-chain` | `target_trade_date + option_product + price_type` | request-scoped read model | [product authority](../products/mo_option_chain/ARCHITECTURE.md) |
| `mo-option-premium-plane` | `as_of + option_product + price_type` | request-scoped `PremiumPlane` | [product authority](../products/mo_option_premium/ARCHITECTURE.md) |

本表是 authority-level semantic catalog：它说明 service identity、input、result/delivery 与 canonical product owner，不是 `services/catalog.py` 的 executable binding table。Repository-wide product/capability discovery 仍从 [Capability Catalog](../../../CAPABILITIES.md) 进入。

Semantic catalog 是显式、静态、authority-driven 的，不通过扫描文件系统动态发现。不做：

```text
dynamic registry
plugin discovery
schema registry
service lifecycle framework
```

`index_daily`、`stock_daily` 仍属于 Source Capture / Raw capability，**不**升级为 Data Service；`index-daily-history` 是复用 `index_daily` 的独立产品语义，不是 Capture 的别名。

`services/catalog.py` 是另一个更窄的概念：它只保存 `dms` 可执行的 persisted-service bindings。一个 request-scoped Data Service 不需要进入该 Python catalog，也不需要适配当前返回 artifact `Path` 的 execution binding。

## 3. Service integration boundary

### 3.1 `csi1000-5d-analysis`

Data Service 拥有该 persisted-artifact service 的 orchestration 与 canonical output publication。产品定位、所需 Capture、Raw scope、窗口、formula 与 `snapshot.json` 内容分别由 [产品入口](../products/csi1000_5d_analysis/ARCHITECTURE.md)、[data authority](../products/csi1000_5d_analysis/data.md) 与 [Preparation authority](../products/csi1000_5d_analysis/preparation-contract.md) 拥有，不在本文档重新定义。

### 3.2 `mo-option-chain`

Data Service 拥有该 request-scoped service 的 application request、orchestration、read-model result 与 classified semantic failure。产品/query identity、Raw scope 与 read semantics 分别由 [产品入口](../products/mo_option_chain/ARCHITECTURE.md)、[data authority](../products/mo_option_chain/data.md) 与 [read contract](../products/mo_option_chain/read-contract.md) 拥有；HTTP projection 由 [backend-api HTTP contract](../../../../backend-api/products/mo_option_chain/http-contract.md) 拥有。

`mo-option-chain` 不使用 `dms get`，V1 也没有 canonical persisted final output；它向 delivery adapter 交付 request-scoped read model 或 classified semantic failure。

### 3.3 `mo-option-premium-plane`

MO Premium Plane product service 拥有该 request-scoped analytical service 的 application request、orchestration、semantic failure classification 与 result boundary。产品定位与 ownership、Source/Raw scope、Basis/Point/Plane semantics、product orchestration 分别由 [产品入口](../products/mo_option_premium/ARCHITECTURE.md)、[data authority](../products/mo_option_premium/data.md)、[backend authority](../products/mo_option_premium/backend.md) 与 [service contract](../products/mo_option_premium/service-contract.md) 拥有；HTTP projection 由 [backend-api HTTP contract](../../../../backend-api/products/mo_option_premium/http-contract.md) 拥有。

`mo-option-premium-plane` 不使用 `dms get`，V1 不要求 canonical persisted final output；它向 delivery adapter 交付 request-scoped `PremiumPlane` 或 classified semantic failure。共享 Data Service authority 不复制其 Capture ordering、financial formulas 或 product failure semantics。

### 3.4 `csi1000-im-basis-history`

CSI1000 IM Basis History product service 拥有显式日期区间 request、Capture/Preparation orchestration、classified semantic failure 与 request-scoped result boundary。产品定位、Source scope、shared IM basis semantics 与 read/application contract 分别由 [产品入口](../products/csi1000_im_basis_history/ARCHITECTURE.md)、[data authority](../products/csi1000_im_basis_history/data.md)、[shared IM basis authority](../preparation/im_basis/ARCHITECTURE.md) 与 [read/application contract](../products/csi1000_im_basis_history/read-contract.md) 拥有。

`csi1000-im-basis-history` 只向 Python consumer 交付 request-scoped `CSI1000IMBasisHistoryResult` 或 classified semantic failure。V1 不使用 `dms get`、不持久化 final result，也没有 HTTP delivery adapter。

### 3.5 `index-daily-history`

Index Daily History product service 拥有指定指数及显式区间的 request、Capture/Preparation orchestration、classified semantic failure 与 request-scoped result boundary。产品身份、Source scope/completeness 与 read/application contract 分别从 [产品入口](../products/index_daily_history/ARCHITECTURE.md)、[data authority](../products/index_daily_history/data.md) 和 [read/application contract](../products/index_daily_history/read-contract.md) 进入。

`index-daily-history` 只向 Python consumer 交付 request-scoped `IndexDailyHistoryResult` 或 classified semantic failure；V1 不使用 `dms get`、不持久化 final result，也没有 HTTP delivery adapter。

## 4. CLI: dms

用户级 CLI 语义名称为 `dms`。第一版只支持两个命令：`list`、`get`。CLI 是 delivery surface 之一，只寻址 CLI executable catalog 中的 persisted-artifact service；当前为 `csi1000-5d-analysis`。`mo-option-chain` 与 `mo-option-premium-plane` 通过 HTTP 暴露，`csi1000-im-basis-history` 与 `index-daily-history` 通过 public Python boundary 交付；这四个 request-scoped Data Services 都不走 `dms get`（见第 3.2–3.5 节）。

### 4.1 dms list

canonical semantic：

```text
dms list
```

作用：

> 列出当前 CLI-addressable Data Services，即 `dms get` 可以 resolve 的 executable entries。

第一版至少输出每个 CLI executable entry 的：

```text
service_id
description
```

结果中应包含：

```text
csi1000-5d-analysis
```

V1 `dms list` 不列出 request-scoped `csi1000-im-basis-history`、`index-daily-history`、`mo-option-chain` 或 `mo-option-premium-plane`；所有 repository products/capabilities 从 [Capability Catalog](../../../CAPABILITIES.md) 发现。CLI executable catalog 不通过扫描文件系统动态发现。

### 4.2 dms get

canonical semantic：

```text
dms get <service_id> --date YYYY-MM-DD
```

当前示例：

```text
dms get csi1000-5d-analysis --date 2026-09-18
```

其中：

```text
--date
```

明确表示：

```text
target_trade_date
```

调用者必须显式提供。当前不支持：

```text
today
latest
yesterday
自动寻找最近交易日
自动 fallback
```

## 5. CLI 与 product orchestration 边界

CLI 只解析参数、校验 CLI-level 输入、从 executable catalog resolve CLI-addressable Data Service、调用并报告结果或错误。当前 executable binding 面向返回 persisted artifact `Path` 的 service；request-scoped services 不需要使用或模拟这个 binding。CLI 不编排 Capture，也不重新定义：

```text
Source semantics
Source Capture semantics
window semantics
derived formula
Analysis-ready Artifact schema
```

产品使用哪些 Capture、执行顺序、Preparation 与 publication 时机由对应 product context 拥有；`csi1000-5d-analysis` 的顺序见其 [product authority](../products/csi1000_5d_analysis/ARCHITECTURE.md)。

## 6. canonical output（persisted-artifact services）

`output/` 是 **persisted-artifact Data Service** 的用户级输出根目录。该约定只适用于以持久化 artifact 为 result semantics 的 service（当前即 `csi1000-5d-analysis`），不是所有 Data Service 的通用规则：

```text
output/
└── <service_id>/
    └── <target_trade_date>/
        └── <service artifact>
```

当前：

```text
output/
└── csi1000-5d-analysis/
    └── 2026-09-18/
        └── snapshot.json
```

因此对于 `csi1000-5d-analysis`：

```text
service_id + target_trade_date
```

唯一确定一次最终用户输出位置。

`csi1000-im-basis-history`、`index-daily-history`、`mo-option-chain` 与 `mo-option-premium-plane` 是 request-scoped results，V1 不要求 canonical persisted final output，不落入上述 `output/<service>/<date>/` 约定（见第 3.2–3.5 节）。

## 7. Raw Artifact / Analysis-ready Artifact / Output 边界

* `data/raw/`：Source Facts / internal runtime artifacts（Raw Artifact）。
* `data/snapshots/`：非 Data Service 的 Analysis-ready Artifact 输出目录。第一版 Daily 数据产品（`data/snapshots/YYYY-MM-DD/snapshot.json`）不是 Data Service，继续使用 `data/snapshots/`。
* `output/<service_id>/<target_trade_date>/`：persisted-artifact Data Service 的 canonical user-facing output。

> `output/<service>/<date>/` 是 persisted-artifact Data Service 的 canonical user-facing output，不适用于 request-scoped results。

Data Service 的 orchestration 把 Analysis Preparation 产出的 artifact 发布到该位置；`data/snapshots/csi1000-5d-analysis/<date>/snapshot.json` 不属于该 service 的输出，也不得维护两份相同 artifact。

Daily Market Snapshot 不是 Data Service，继续使用 `data/snapshots/YYYY-MM-DD/`，不与 Data Service output 合并。

## 8. 日粒度语义（csi1000-5d-analysis）

对于 persisted-artifact service `csi1000-5d-analysis`，每次：

```text
get <service> --date D
```

代表一个按日的数据服务请求。

运行单元：

```text
service_id
+
target_trade_date
```

对应：

```text
output/<service_id>/<target_trade_date>/
```

需要明确：

> “按日”描述的是 `csi1000-5d-analysis` 的 request / output partition，不表示所有内部 Raw Artifact 只能包含一天数据，也不推广为所有 Data Service 的通用 result semantics。

例如：

```text
index_daily_history.json
im_futures_daily.json
```

可以包含多个历史交易日。但它们都属于 `target_trade_date = D` 这一次数据准备。`csi1000-im-basis-history`、`index-daily-history`、`mo-option-chain` 与 `mo-option-premium-plane` 是 request-scoped results，不适用本节的按日持久化 partition 语义（见第 3.2–3.5 节）。

## 9. Non-goals

不要设计：

```text
scheduler / cron / database / generic API platform

plugin system / dynamic registry / workflow engine / dependency graph framework

retry framework / cache framework

automatic latest trading date / automatic scheduling

GPT analyzer / trading analysis
```

保持第一版极小。

## 10. HTTP delivery boundary

HTTP inbound delivery 的 canonical owner 是 [backend-api](../../../../backend-api/ARCHITECTURE.md)。通用 API platform（多租户、通用 endpoint、auth、版本化、schema registry 等）不属于当前范围。

MO Option Chain 与 MO Premium Plane 通过各自的 HTTP delivery adapter 读取数据；Option Chain 前端语义见 [web-ui visualization authority](../../../../web-ui/src/features/mo_option_chain/ARCHITECTURE.md)，Premium transport 见其 product HTTP contract。

HTTP delivery adapter 与 CLI 的关系：

```text
                 ┌─ CLI
Data capability ─┤
                 └─ HTTP delivery adapter
```

两者都是 delivery surfaces，都不是业务语义 owner。

HTTP delivery adapter 不拥有：

```text
Source Capture orchestration semantics
Source endpoint semantics
Preparation formulas
market modeling
```

本文档不定义：

```text
FastAPI folder structure
endpoint URL
HTTP method
request schema
response JSON schema
OpenAPI model
API versioning
auth
CORS policy
server deployment
```

这些属于具体产品的 HTTP delivery contract 或实现设计。MO Option Chain transport 见 [backend-api HTTP contract](../../../../backend-api/products/mo_option_chain/http-contract.md)，MO Premium Plane transport 见 [backend-api HTTP contract](../../../../backend-api/products/mo_option_premium/http-contract.md)。

## 11. 完成自检

仅阅读相关 authority（`market-snapshot/ARCHITECTURE.md`、本文档及本文档引用的 Guide）应能明确回答：

1. 什么是 Data Service？
2. 当前有哪些 semantic Data Services，从哪里发现？
3. `csi1000-5d-analysis`、`csi1000-im-basis-history` 与 `index-daily-history` 分别表示什么？
4. `dms list` 列出全部 repository products，还是仅 CLI-addressable services？
5. CLI executable catalog 与 Data Service semantic catalog 有什么区别？
6. 如何通过 `dms get` 请求 persisted service？
7. `--date` 的语义是什么？
8. 一次调用最终写到哪里？
9. `data/raw` 与 `output` 有什么区别？
10. 为什么调用方不需要知道底层 Source Capture？
11. `data/snapshots` 与 Data Service canonical output 有什么边界？
12. Request-scoped Data Service 是否必须进入 Path-returning CLI binding？
13. Public Python boundary、HTTP delivery adapter 与 CLI 如何保持各自边界，而不成为产品语义 owner？

若这些问题仍需 implementation agent 自行发明，则本 authority 未完成。
