# guides/data-services.md — Data Service / CLI / output contract authority

> 状态：authority。本文档定义项目最上层的用户调用语义单位 Data Service、用户级 CLI（`dms`）的语义，以及 Data Service 的 canonical user-facing output。
>
> 层级：本文档位于 `market-snapshot/ARCHITECTURE.md` 之下。架构层面的稳定边界以 `market-snapshot/ARCHITECTURE.md` 为准（尤其第 0 节术语、第 2 节核心架构、第 3 节 Raw/Preparation 边界、第 8 节 Guide 职责、第 9 节项目结构）。本文档定义 Data Service 的清单、调用契约与输出契约；具体 Source Capture / Raw Artifact / Analysis Preparation 语义继续由对应 Guide 负责，不在本文档重复。

## 1. 什么是 Data Service

Data Service 是用户可直接请求的完整数据能力。一个 Data Service 可以由多个 Source Capture、Raw Artifact 与 deterministic Analysis Preparation 共同生成。

关系：

```text
Data Service
    ↓
orchestrates existing Source Capture / Analysis Preparation
    ↓
final dated output
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

它只是最上层的**用户调用语义单位**。每个 Data Service 拥有自己的 query identity 与 result semantics，由 catalog 逐项定义，不共用同一个 `service_id + target_trade_date` 模板。用户和 Agent 不需要知道底层有哪些 Source Capture，只需要按该 service 自己定义的 query identity 指定输入。

## 2. Data Service Catalog

Catalog 当前声明两项已实现的 Data Service，不为了丰富 catalog 创造其他服务：

| service_id | description | input | output | 状态 |
| --- | --- | --- | --- | --- |
| `csi1000-5d-analysis` | 为外部 analyzer 分析中证1000未来约 5 个交易日市场状态准备的 analysis-ready 数据产品 | `target_trade_date`（CLI 的 `--date`） | `snapshot.json` | 已实现 |
| `mo-option-chain` | 目标交易日的完整 MO 中证1000股指期权链 deterministic read model（与 `csi1000-5d-analysis` 并列，不依赖其 output） | `target_trade_date` + `option_product` + `price_type` | option-chain read model（`guides/mo-option-chain.md`） | 已实现，通过 HTTP 提供 |

Catalog 是显式、静态、authority-driven 的，不通过扫描文件系统动态发现。不做：

```text
dynamic registry
plugin discovery
schema registry
service lifecycle framework
```

`index_daily`、`stock_daily` 仍属于 Source Capture / Raw capability，**不**升级为 Data Service。

## 3. service 语义

### 3.1 service: csi1000-5d-analysis

语义：

> 为外部 analyzer 分析中证1000未来约 5 个交易日市场状态准备的 analysis-ready 数据产品。

它复用当前已经存在的：

```text
CSI1000 history（Source Capture index_daily，000852.SH）
MO option chain（Source Capture mo_option_basic + mo_option_daily）
IM futures（Source Capture im_futures_basic + im_futures_daily）
deterministic Analysis Preparation（guides/csi1000-5d-analysis-snapshot.md）
```

最终 artifact：`snapshot.json`。

相关 authority：

* Source Capture / Raw Artifact 契约：`guides/csi1000-5d-analysis-data.md`
* Analysis Preparation Definition（Raw → `snapshot.json`）：`guides/csi1000-5d-analysis-snapshot.md`

Data Service 不重新定义 Source semantics / Source Capture semantics / window semantics / derived formula / Analysis-ready Artifact schema；这些继续由上述 Guide 负责。

### 3.2 service: mo-option-chain

语义：

> 目标交易日的完整 MO 中证1000股指期权链 deterministic read model，是与 `csi1000-5d-analysis` 并列的独立数据产品。

输入（query identity，见 `guides/mo-option-chain.md` 第 3 节）：

```text
target_trade_date   required
option_product      required
price_type          optional（缺省 = close）
```

它：

```text
不依赖 csi1000-5d-analysis 的 output（snapshot.json）
不要求 CSI1000 120 日历史分析窗口 / IM 历史分析窗口 / CSI1000 analysis 派生指标
需要目标日 CSI1000 underlying fact 与目标日有效 IM 普通月合约 facts
每个 MO expiry 需要唯一且可用的目标日 IM futures reference
复用共享 Source Capture capability（index_daily / mo_option_basic / mo_option_daily / im_futures_basic / im_futures_daily 的 target-date capability）
```

完整语义的 authority 落点：

```text
query identity / product / underlying / invariants     → guides/mo-option-chain.md
Source / Raw / universe / completeness                 → guides/mo-option-chain-data.md
price / null / grouping / ordering / response / failure → guides/mo-option-chain-read-contract.md
```

本 catalog 不重复定义。

result semantics：`mo-option-chain` 通过 Source Capture → goal-scoped Raw → Analysis Preparation 产生 request-scoped read model，并由 HTTP delivery adapter 提供；V1 无 canonical persisted final output（区别于 `csi1000-5d-analysis` 的 `output/<service>/<date>/snapshot.json`）。

delivery surface：`mo-option-chain` 通过 HTTP read contract 面向 `web-ui`，不使用当前 CLI `dms get` 的 `--date` 单参数形态；transport 语义见 `guides/mo-option-chain-http-contract.md`。

## 4. CLI: dms

用户级 CLI 语义名称为 `dms`。第一版只支持两个命令：`list`、`get`。CLI 是 delivery surface 之一；当前只服务 persisted-artifact service `csi1000-5d-analysis`，`mo-option-chain` 通过 HTTP 提供（见第 3.2、13 节），不走 `dms get`。

### 4.1 dms list

canonical semantic：

```text
dms list
```

作用：

> 列出当前仓库支持的 Data Service。

第一版至少输出每项 Data Service 的：

```text
service_id
description
```

结果中应包含：

```text
csi1000-5d-analysis
```

Catalog 不通过扫描文件系统动态发现。

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

## 5. get 的职责（orchestration）

对于：

```text
dms get csi1000-5d-analysis --date D
```

Data Service 负责 orchestration；CLI 负责解析参数、校验 CLI-level 输入、resolve Data Service、调用 Data Service，并报告结果 / 错误：

```text
D
↓
run CSI1000 history Capture
↓
run MO option basic Capture
↓
run MO option daily Capture
↓
run IM futures basic Capture
↓
run IM futures daily Capture
↓
run Analysis Preparation (build analysis-ready artifact)
↓
publish final Data Service output
```

CLI 不编排 Capture，不重新定义：

```text
Source semantics
Source Capture semantics
window semantics
derived formula
Analysis-ready Artifact schema
```

这些继续由已有 authority 负责。CLI 不应该知道"需要五个 Capture"、"opt_basic 应如何调用"、"Preparation 有哪些 derived fields"、"Capture 执行顺序的业务细节"；这些属于 Data Service orchestration。

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

`mo-option-chain` 是 request-scoped read model，V1 不要求 canonical persisted final output，不落入上述 `output/<service>/<date>/` 约定（见第 3.2 节）。

## 7. Raw Artifact / Analysis-ready Artifact / Output 边界与 reconciliation

* `data/raw/`：Source Facts / internal runtime artifacts（Raw Artifact）。继续不变，见 `market-snapshot/ARCHITECTURE.md` 第 3、9 节。
* `data/snapshots/`：非 Data Service 的 Analysis-ready Artifact 输出目录。第一版 Daily 数据产品（`data/snapshots/YYYY-MM-DD/snapshot.json`）不是 Data Service，继续使用 `data/snapshots/`。
* `output/<service_id>/<target_trade_date>/`：Data Service 的 canonical user-facing output。

reconciliation（当前 CSI1000 Data Service）：

> `output/<service>/<date>/` 是 Data Service 的 canonical user-facing output。

Data Service 的 orchestration 把 Analysis Preparation 产出的 artifact 发布到该位置（`src/daily_market_snapshot/services/csi1000_5d_analysis.py`）；`data/snapshots/csi1000-5d-analysis/<date>/snapshot.json` 不再产生，不维护两份相同 artifact。

本 Goal 不重构无关的第一版 Daily 数据产品；`data/snapshots/YYYY-MM-DD/` 语义保持不变。

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

可以包含多个历史交易日。但它们都属于 `target_trade_date = D` 这一次数据准备。`mo-option-chain` 是 request-scoped read model，不适用本节的按日持久化 partition 语义（见第 3.2 节）。

## 9. Git boundary

锁定以下均为 runtime artifacts：

```text
.env
data/raw/**
output/**
```

它们不得进入 Git history。（`data/snapshots/**` 也继续作为运行产物，不进入版本控制。）

仓库只版本化：

```text
code
authority / guides
tests
configuration templates
```

不记录每日市场数据产品。

## 10. Agent execution surface

锁定：

> Data Service CLI 是普通用户和 Agent 执行数据任务的 canonical interface。

以后用户要求：

```text
生成 2026-09-18 的 csi1000-5d-analysis
```

Agent 应优先执行语义等价于：

```text
dms get csi1000-5d-analysis --date 2026-09-18
```

而不是自行逐个寻找 Capture。

底层 Source Capture / Analysis Preparation 可以继续存在，用于：

```text
development
debugging
testing
reconciliation
```

但不是普通用户主入口。

## 11. CLI implementation surface

当前仓库仍使用 Poetry `package-mode = false`。本文档只锁定 CLI **语义名称** `dms`，不要求 package 化，不提前要求生成系统级 executable。

第一版 implementation 可以自然落成：

```text
poetry run python scripts/dms.py list
```

```text
poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
```

它们在语义上分别是：

```text
dms list
dms get ...
```

是否增加真正的 `dms` console entry point 保持 deferred。

## 12. Non-goals

不要设计：

```text
scheduler / cron / database / generic API platform

plugin system / dynamic registry / workflow engine / dependency graph framework

retry framework / cache framework

automatic latest trading date / automatic scheduling

GPT analyzer / trading analysis
```

保持第一版极小。

## 13. HTTP delivery boundary

通用 API platform（多租户、通用 endpoint、auth、版本化、schema registry 等）不属于当前范围。

第一个 Web vertical slice（MO option-chain visualization，见 `web-ui/guides/mo-option-chain-visualization.md`）通过最小 HTTP delivery adapter 读取数据。

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

这些属于 HTTP delivery contract / implementation design：`mo-option-chain` 的最小 HTTP transport contract 已落在 `guides/mo-option-chain-http-contract.md`（Stage 2）。

最小 HTTP delivery adapter 采用 FastAPI 实现（`src/daily_market_snapshot/api/`）。

## 14. Deferred

```text
真正 dms console entry point
```

## 15. 完成自检

仅阅读相关 authority（`market-snapshot/ARCHITECTURE.md`、本文档及本文档引用的 Guide）应能明确回答：

1. 什么是 Data Service？
2. 当前有哪些 Data Service？
3. `csi1000-5d-analysis` 表示什么？
4. 如何列出 service？
5. 如何请求 service？
6. `--date` 的语义是什么？
7. 一次调用最终写到哪里？
8. `data/raw` 与 `output` 有什么区别？
9. 哪些文件不进入 Git？
10. 为什么普通用户/Agent 不需要知道底层 Source Capture？
11. 现有 `data/snapshots` 与新的 canonical output 如何 reconciliation？
12. HTTP delivery adapter 与 CLI 是否都是 delivery surfaces，而不是业务语义 owner？

若这些问题仍需 implementation agent 自行发明，则本 authority 未完成。
