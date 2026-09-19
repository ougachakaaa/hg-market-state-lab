# ARCHITECTURE.md — market-snapshot 模块架构 authority

本文件定义 `market-snapshot` 模块的架构层面 authority。

它只描述理解本模块所必需的核心目标、语义与边界。具体的数据需求、执行规则和实现细节放在对应的下层文档或 Guide 中（见第 8 节与第 13 节），按需读取。

本模块在仓库顶层的定位、职责边界与数据流见根 `ARCHITECTURE.md`。本文件只负责 `market-snapshot` 内部架构。

---

## 0. 术语

全文固定使用以下术语，不做同义替换：

| 术语 | 含义 |
| --- | --- |
| Data Service | 用户可直接请求的完整数据能力（最上层用户调用语义单位），负责 orchestration |
| Source | 项目外部的数据提供方，定义其自身的数据事实与 API 语义 |
| Source Capture | 按 Source 自身语义获取并保存事实数据的组件 |
| Raw Artifact | Source Capture 的持久化输出，保留 Source 事实语义，允许 minimal normalization |
| Analysis Preparation | 根据明确的 Analyzer 数据需求，对 Raw Artifact 进行的确定性分析准备 |
| Analysis-ready Artifact | Analysis Preparation 的输出 |
| CLI | Data Service 的用户接口，不是业务架构层 |
| Analyzer | 本模块之外、消费 Analysis-ready Artifact 的外部分析方 |

`Dataset`、`Snapshot`、`Snapshot Assembly`、`Snapshot Definition` 不再是本模块的通用 Architecture Concept。这些词在具体 artifact 文件名（`snapshot.json`）或历史 Guide 文件名中仍可能保留，但不承担通用架构层的语义。

---

## 1. Purpose

`market-snapshot` 模块负责：从外部市场数据 Source 捕捉事实，并按照明确的数据需求进行确定性数据准备，生成 analysis-ready artifacts。

第一个数据产品阶段建立最小可运行闭环：

```text
Source
    ↓
Source Capture
    ↓
Raw Artifact
    ↓
Analysis Preparation
    ↓
Analysis-ready Artifact
    ↓
External Analyzer
```

本阶段重点不是建设通用数据平台，而是建立简单、明确、容易扩展的数据边界。

### 1.1 Responsibility Boundary

本模块的职责止于产生结构化、可复现、可分析（analysis-ready）的市场数据（Source → Raw Artifact → Analysis-ready Artifact）。第 1 节流程图中最后一步 "External Analyzer" 属于外部 analyzer，不属于本模块。

业务分析及其规则（例如价格中枢、噪声区、期权反向交易候选区域、bullish / bearish 判断、交易信号、目标点位等结论）属于外部 analyzer，不进入本模块的数据契约，也不得作为本模块 Analysis Preparation 的业务逻辑实现。

分析目标可以作为数据需求（Raw Artifact / Analysis-ready Artifact definition）的来源，驱动本模块确定"需要哪些数据"；但分析规则与结论不由本模块定义或执行。

---

## 2. Core Architecture

第一阶段的模块核心模型以职责划分，Data Service 是面向用户的最上层调用语义单位：

```text
Data Service
    ↓
orchestrates
    ├─ Source Capture → Raw Artifact
    └─ Analysis Preparation ← Raw Artifact
            ↓
   Analysis-ready Artifact
```

### Data Service

用户可直接请求的完整数据能力。Data Service 负责 orchestration：

```text
target_trade_date
    ↓
required Source Captures
    ↓
Raw Artifacts
    ↓
required Analysis Preparation
    ↓
canonical Analysis-ready Artifact
```

Data Service 不定义 Source API 细节，也不实现 Preparation formula。具体 service 清单、输入/输出契约与 CLI 语义定义在 `guides/data-services.md`。

### Source

模块外部的数据提供方。

例如：

* Tushare

Source 定义其自身的数据事实和 API 语义，负责提供数据，不定义最终 Analysis-ready Artifact 的组织形式。

### Source Capture

负责按照 Source 自身语义获取并保存事实数据。

职责：

```text
具体 endpoint 调用
query parameters
Source-domain scope selection
minimal normalization
Raw Artifact production
```

Source Capture 可以知道：

```text
这是 MO
这是 IM
这是 CFFEX
某合约是否在生命周期内
目标 trade_date 是什么
```

因为这些属于 Source fact / capture scope。

Source Capture 不可以知道：

```text
Analyzer 想判断什么
哪个 strike 更值得分析
哪个合约流动性更好
未来中枢在哪里
是否适合卖 Call / Put
```

判断原则：

> 如果一个处理步骤仅需要理解 Source 及本次采集目标，它属于 Source Capture；如果必须知道 Analyzer 为什么需要这些数据，它属于 Analysis Preparation。

### Raw Artifact

Source Capture 的持久化输出。

例如：

```text
index_daily_history.json
mo_option_basic.json
mo_option_daily.json
im_futures_basic.json
im_futures_daily.json
```

Raw Artifact：

```text
保留 Source 事实语义
允许 minimal normalization
不包含 analyzer-specific interpretation
```

Raw Artifact 是层之间的数据契约，不是独立业务层。

### Analysis Preparation

根据明确的 Analyzer 数据需求，对 Raw Artifact 进行确定性的分析准备。

允许：

```text
window selection
join
projection
analysis-oriented rename
restructure

return
SMA
ATR
realized volatility
moneyness
normalized premium
basis
annualized basis
```

这些操作的共同特征是：

```text
same Raw Artifact
+
same Preparation Definition
=
same output
```

Analysis Preparation 不负责业务判断。

禁止：

```text
future center
noise zone
market regime
bullish / bearish
sell call / sell put
recommended strike
target price
probability
trading recommendation
```

最核心边界：

> Analysis Preparation prepares data for analysis; it does not perform the analysis.

### Analysis-ready Artifact

Analysis Preparation 的输出。

例如当前：

```text
output/csi1000-5d-analysis/<date>/snapshot.json
```

Analysis-ready Artifact 是通用架构术语。当前文件继续叫 `snapshot.json`，不在本轮修改输出文件名。`snapshot.json` 可以作为某个具体 Data Service 的 artifact 名称继续存在，但 Snapshot 不再是本模块核心 Architecture Layer。

### CLI

CLI 是 Data Service 的用户接口，不是业务架构层。

职责：

```text
parse arguments
validate CLI-level input
resolve Data Service
invoke Data Service
report result / error
```

CLI 不应该知道：

```text
需要五个 Capture
opt_basic 应如何调用
Preparation 有哪些 derived fields
Capture 执行顺序的业务细节
```

这些属于 Data Service orchestration。

### 依赖方向

代码组件之间的依赖方向是单向的：

```text
CLI → Data Service

Data Service → Source Capture
Data Service → Analysis Preparation

Source Capture → Source
Analysis Preparation → Raw Artifact（层间 contract）
```

Raw Artifact 与 Analysis-ready Artifact 是层间数据契约 / persisted artifact，不是业务代码层：

```text
Source Capture produces Raw Artifact
Analysis Preparation consumes Raw Artifact
Analysis Preparation produces Analysis-ready Artifact
```

* Data Service 依赖 Source Capture 与 Analysis Preparation，通过 orchestration 把它们串起来。
* Analysis Preparation 依赖 Raw Artifact contract，不得依赖 Source，也不得在准备阶段发起采集。
* Source Capture 依赖 Source，不得依赖 Analysis Preparation 的输出结构。
* Data Service 不重新定义 Source / Source Capture / Analysis Preparation 的语义；其具体内容由 `guides/data-services.md` 与对应 Guide 承载。

### Multiple Data Products（共享 Capture 能力的多个数据产品）

本模块可以在同一套 Source / Source Capture capability 之上，暴露多个**并列**的 deterministic data product / preparation。

当前两个 sibling downstream preparations：

```text
Shared Source facts / Capture capabilities
      ├→ CSI1000 5D Analysis Preparation  → analysis-ready artifact
      └→ MO Option Chain Preparation       → option-chain read model
```

* MO Option Chain 与 CSI1000 5D Analysis 并列，互不依赖彼此的最终 artifact。尤其 MO Option Chain 不依赖 `csi1000-5d-analysis` 的 analysis-ready artifact（`snapshot.json`），也不要求 120 日历史窗口、IM futures 或 CSI1000 分析派生指标。
* **shared Capture capability ≠ shared goal-scoped Raw Artifact**：Capture 组件语义可复用，但每个 data product 拥有自己的 goal-scoped Raw Artifact，不互相读取对方的 Raw。
* MO Option Chain 的 `option-chain read model` 是面向 read / visualization 消费方的确定性输出，仍由 Analysis Preparation 从 Raw Artifact 产生，不引入新的通用架构层。
* 具体字段、分组、排序、价格与失败语义不进入本文件，由 `guides/mo-option-chain.md`（入口）及其子 Guide `guides/mo-option-chain-data.md`、`guides/mo-option-chain-read-contract.md` 承载。

---

## 3. Raw Artifact 与 Analysis-ready Artifact 的边界

本模块必须明确区分：

```text
Raw Artifact
```

和：

```text
Analysis-ready Artifact
```

### Raw Artifact

Raw Artifact 表示从数据源获取的数据事实。

主要职责是：

```text
Source
    ↓
API Call
    ↓
minimal normalization
    ↓
Raw Artifact File
```

Raw 层应尽量避免包含针对某个具体 Analysis Preparation 的组织逻辑。

#### minimal normalization 的判据

采集层允许的操作：

* 统一日期格式（例如统一为 `YYYY-MM-DD`）；
* 按源语义归一字段名；
* 数值类型转换（例如字符串数字转为数字）；
* 按源返回顺序或源主键排序；
* 原样保留源返回的全部行。

采集层不允许的操作：

* 按分析主题过滤或重排行；
* 把字段重命名为分析视角的名称；
* 按分析概念合并、拆分或派生字段；
* 补充源未返回的计算指标；
* 丢弃源返回的行。

判断标准：若某项处理需要知道"这个 Analysis-ready Artifact 要用它做什么"，则它属于 Analysis Preparation，不属于采集层。

补充（Source-domain scope selection 属于 Capture）：Source Capture 可以基于 Source facts 选择自己定义的事实范围。例如 Tushare `opt_daily(exchange=CFFEX)` 同时返回 IO / HO / MO 时，`mo_option_daily` Capture 可以选择 MO universe。这属于 Capture scope，不属于分析过滤。

### Analysis-ready Artifact

Analysis-ready Artifact 是 Raw Artifact 的下游组织结果：

```text
Raw Artifact A
Raw Artifact B
Raw Artifact C
      ↓
Analysis Preparation
      ↓
Analysis-ready Artifact
```

Analysis-ready Artifact 可以频繁调整，而不要求重新设计数据采集层。

### 语义规则

* 原始数据不做分析层解读。
* Analysis-ready Artifact 只能包含 Raw Artifact 的下游组织结果，不得包含只存在于 Analysis-ready Artifact 中且无法回溯到 Raw Artifact 的数据事实。

因此：

> Source Capture 负责获得事实，Analysis Preparation 负责按照当前分析需求组织事实。

这是第一阶段最重要的架构边界。

---

## 4. 架构边界的执行

架构边界在运行时的直接推论：

* Analysis Preparation 只从本地 Raw Artifact 准备数据，不得在准备阶段直接发起采集（调用 Source）。
* Capture 与 Preparation 的具体写入、覆盖、重跑与失败处理属于实现策略，不由本文件预设；需要时由对应 Guide 明确。

---

## 5. Extensibility Model

本模块需要支持分析需求不断扩展，但第一阶段不引入插件框架、复杂抽象或通用 Pipeline 系统。

横向扩展采用最简单的方式。

### 增加新的数据内容

当分析需要新的市场数据时：

```text
Identify required Source Capture
    ↓
Add Source Capture
    ↓
Generate Raw Artifact
    ↓
Include Raw Artifact in Analysis Preparation if needed
```

新增 Source Capture 不应要求重构已有 Source Capture。

### 调整 Analysis-ready Artifact 内容

如果新的分析需要增加字段、删除字段、增加 Raw Artifact、改变分类方式，主要修改 Analysis Preparation 和相关 Guide。

Raw Artifact 不应因为单纯的输出结构调整而改变。

### 调整 Analysis-ready Artifact 输出格式

Analysis-ready Artifact 可以从 `snapshot.json` 演进为多个文件或其他更适合分析的组织方式。Analysis-ready Artifact 输出结构不是本模块长期固定 API。

---

## 6. Reproducibility

虽然 Analysis-ready Artifact 的定义允许演进，但同一个已经确定的 Preparation Definition 应该能够稳定重复执行：

```text
same Raw Artifact
+
same Preparation Definition
=
same Analysis-ready Artifact
```

当分析需求发生变化时，可以形成新的 Preparation Definition。

因此本模块追求的不是永久固定的 artifact schema，而是对当前已经确定的数据需求，能够稳定、明确、可复现地生成 Analysis-ready Artifact。

### Preparation Definition 的 authority 落点

Preparation Definition 的 authority 是 `guides/` 中对应的 Guide（当前为 `guides/csi1000-5d-analysis-snapshot.md`）。该 Definition 的实现位于 `src/daily_market_snapshot/preparation/`（当前为 `csi1000_5d_analysis.py`）：它按照 Guide 读取 Raw Artifact 并完成 Analysis Preparation，不构成 authority，不得反向定义或修改 Preparation Definition。实现与 Guide 不一致时，必须对实现做 reconciliation，不得静默改变语义。

本阶段不引入额外的 schema 定义文件、registry 或版本管理框架。

### 可复现性要求

Analysis-ready Artifact 的结果只依赖该交易日的 Raw Artifact 与当前 Preparation Definition。

不得依赖运行时刻、网络状态、随机性或本地缓存残留。

---

## 7. Agent-oriented Workflow

本模块允许 Agent 参与数据需求实现和 Analysis Preparation 组织。

推荐工作方式：

```text
Human / Analyst
      ↓
Define or change data requirement
      ↓
Authority / Guide
      ↓
Agent
      ↓
Implement required Source Capture / Analysis Preparation change
      ↓
Run and verify
```

Agent 可以承担：

* 根据数据需求识别需要的 Source Capture；
* 添加新的 Source Capture；
* 调整 Analysis Preparation；
* 调整输出结构；
* 增加必要测试；
* 更新相关 Guide。

但是 Agent 不应自行改变已经确定的业务语义。

已经确定的业务语义包括：

* Source Capture 的含义与职责；
* Analysis Preparation 的内容定义；
* 输出的语义；
* Capture 与 Preparation 之间的职责边界。

上述变更必须先更新 authority（本文件或对应 Guide），再修改实现。

---

## 8. Guide Responsibility

`guides/` 用于描述具体的数据需求和可执行 workflow。

Guide 可以说明：

* 当前 Analysis-ready Artifact 需要哪些数据；
* Source Capture 对应什么数据源；
* Analysis Preparation 如何组织这些 Raw Artifact；
* 如何运行采集；
* 如何生成 Analysis-ready Artifact；
* 如何检查结果。

Guide 是 Agent 执行具体任务时的重要上下文。

架构 authority 定义稳定边界；Guide 定义当前任务和当前数据产品的具体需求。

两者职责不同：

| | authority（本文件） | Guide（`guides/`） |
| --- | --- | --- |
| 定义 | 稳定边界与核心语义 | 当前任务与当前数据产品的具体需求 |
| 变化频率 | 低 | 随分析需求变化 |
| 内容 | Source / Source Capture / Raw Artifact / Analysis Preparation 的职责与分层规则 | 需要哪些数据、如何采集、如何准备、如何检查 |
| 优先级 | 冲突时以本文件为准 | 不得与本文件冲突 |

约束：

* Guide 不得与 authority 冲突，也不得引入新的架构概念。
* 出现冲突时以本文件为准。

---

## 9. Project Structure

本模块结构以职责分层。目标是：

```text
market-snapshot/
│
├─ src/
│  └─ daily_market_snapshot/
│     │
│     ├─ cli.py
│     ├─ artifacts.py
│     │
│     ├─ sources/
│     │  └─ tushare.py
│     │
│     ├─ capture/
│     │  ├─ common.py
│     │  ├─ index_daily.py
│     │  ├─ stock_daily.py
│     │  ├─ csi1000_index_history.py
│     │  ├─ mo_option_basic.py
│     │  ├─ mo_option_daily.py
│     │  ├─ im_futures_basic.py
│     │  └─ im_futures_daily.py
│     │
│     ├─ preparation/
│     │  └─ csi1000_5d_analysis.py
│     │
│     ├─ services/
│     │  ├─ catalog.py
│     │  ├─ csi1000_5d_analysis.py
│     │  └─ mo_option_chain.py
│     │
│     └─ api/
│        ├─ app.py
│        ├─ endpoint.py
│        ├─ schemas.py
│        └─ errors.py
│
├─ scripts/
│  ├─ dms.py
│  └─ api.py
│
├─ guides/
├─ config/
├─ data/
├─ output/
└─ tests/
```

各目录职责：

* `src/daily_market_snapshot/cli.py`：CLI（argparse、`list` / `get`、输入校验、service lookup、结果/错误呈现），不编排 Capture。
* `src/daily_market_snapshot/artifacts.py`：真正共享的本地 artifact 能力（canonical roots、JSON read/write、Raw/output path construction），保持很薄，不发展为 storage framework。
* `src/daily_market_snapshot/sources/tushare.py`：最薄的 Tushare integration——credential / token 读取、client creation、Source-specific representation / date conversion，以及真正通用的 Tushare helper。不承担具体 Capture 的 endpoint query orchestration，不建立通用 DataSource framework。
* `src/daily_market_snapshot/capture/`：Source Capture 实现（具体 endpoint 调用、query parameters、Source-domain scope selection、minimal normalization、Raw facts）。
* `src/daily_market_snapshot/preparation/`：Analysis Preparation 实现（确定性的 Raw → analysis-ready 转换）。
* `src/daily_market_snapshot/services/catalog.py`：显式静态 catalog，不做 dynamic registry / filesystem discovery。
* `src/daily_market_snapshot/services/csi1000_5d_analysis.py`：Data Service orchestration（Capture 编排、Preparation 调用、失败边界、最终 artifact 发布）。
* `src/daily_market_snapshot/services/mo_option_chain.py`：Data Service `mo-option-chain` 的 application boundary——read-model 数据结构、query identity 输入与失败类型；HTTP delivery adapter 只通过它获取 read model，不读 Raw、不调 Source（真实 provider 实现 deferred）。
* `src/daily_market_snapshot/api/`：最小 HTTP delivery adapter。它只做 transport，不拥有 market semantics。内部职责：
  * `app.py`：FastAPI application composition、exception handlers、OpenAPI 发布；
  * `endpoint.py`：MO Option Chain HTTP endpoint、dependency wiring、read model → transport 映射；
  * `schemas.py`：Pydantic request / response transport DTO（含 request-shape 校验）；
  * `errors.py`：error envelope、transport error kind 闭集与 HTTP status mapping。
  字段级 HTTP contract 不在本文件，见 `guides/mo-option-chain-http-contract.md`。
* `scripts/dms.py`：极薄 executable shim，转发到 `cli.py`。
* `scripts/api.py`：极薄 executable shim，启动 HTTP delivery adapter（默认 `127.0.0.1:8011`，可用 `--host` / `--port` 覆盖；bind address 属于 launcher / deployment 细节，不属于 HTTP transport contract）。
* `guides/`：描述具体数据需求与可执行 workflow。
* `config/`：非敏感的运行配置。凭据（例如 `TUSHARE_TOKEN`）只从环境变量读取，不进 `config/`，不进版本控制。
* `data/raw/`：Raw Artifact 输出目录。
* `output/`：**persisted-artifact Data Service** 的 canonical user-facing output root（`output/<service_id>/<target_trade_date>/`），当前适用于 `csi1000-5d-analysis`。它不是所有 Data Service 的通用规则：`mo-option-chain` 的 result semantics 是 request-scoped read model，经 HTTP delivery 提供结果，V1 不要求把最终 artifact 写入 `output/`（见 `guides/data-services.md` 第 3.2、6 节）。
* `tests/`：测试。

`data/raw/` 与 `output/` 是运行产物，不进入版本控制。

reconciliation 说明：上述目标结构已于 implementation reconciliation 落地。实现位于 `src/daily_market_snapshot/`（`sources/tushare.py`、`capture/`、`preparation/`、`services/`、`api/`、`artifacts.py`、`cli.py`），`scripts/dms.py` 转发到 `cli.py`、`scripts/api.py` 启动 `api/`，两者都只是极薄 executable shim。Python package 当前仍叫 `daily_market_snapshot`（repository 目录名 `market-snapshot` 与 Python package 名 `daily_market_snapshot` 是两个独立事实，本文件不把二者混为一谈）。Poetry 仍为 `package-mode = false`，因此该结构通过 `pytest` 的 `pythonpath` 与 mypy 的 `mypy_path` 指向 `src/`，而不是通过打包安装。

---

## 10. Non-goals

第一阶段不主动建设：

* 数据库；
* 实时行情系统；
* 分布式采集；
* 通用工作流引擎 / Pipeline framework；
* DataSource framework；
* Plugin / Registry framework；
* Repository pattern / DDD / Clean Architecture；
* 第二个 Source；
* 复杂 Schema version framework；
* 通用 ETL 平台。

同时，以下内容也不属于第一阶段范围：

* Capture 与 Preparation 之间的通用参数化配置层；
* 跨 Raw Artifact 的原始数据重试、缓存或版本化策略；
* Capture 的调度、增量更新与自动化编排。

只有当实际需求产生足够复杂度时，才重新评估是否需要这些能力。

reconciliation：`mo-option-chain` 已在 Stage 1 authority 中声明为第二个 Data Service（见 `guides/data-services.md` 与 `guides/mo-option-chain.md`）；其 preparation / delivery 实现属于下一阶段，本阶段不建设，因此“第二个 Data Service”不再列入 Non-goal。

reconciliation：`guides/data-services.md` 第 13 节早先把 `API server` 整体列为 Non-goal，那是指**通用 API platform**。为第一个明确的 Web vertical slice（MO option-chain visualization）已增加**最小 HTTP delivery adapter**（`api/`，FastAPI），其 transport 契约由 `guides/mo-option-chain-http-contract.md` 拥有。通用 API platform（多租户、auth、versioning、schema registry、通用 endpoint 框架）仍然是 Non-goal。

---

## 11. Design Principles

第一阶段遵循以下原则：

### Keep it simple

优先选择能够完成当前需求的最直接实现。

### Semantics before implementation

涉及 Source Capture 职责、Analysis Preparation 内容、输出结构和职责边界时，先明确设计，再修改实现。

### Authority before code

已经落入本模块 authority 的设计优先于一般工程惯例。

如果代码与 authority 不一致，应明确进行 reconciliation，而不是静默改变语义。

### Stable boundaries, flexible content

Source、Source Capture、Analysis Preparation 与 Data Service 各层边界应保持清晰。

具体 Capture 数量、Analysis-ready Artifact 内容和输出结构允许持续变化。

### Agent-friendly

本模块结构、Guide 和实现应保持足够直接，使 Agent 能够通过阅读有限上下文理解并修改本模块。

不要为了扩展性提前增加会扩大 Agent 理解成本的抽象。

---

## 12. Success Criterion

第一阶段完成时，应能够：

```text
given a trading date
        ↓
run the required Source Captures
        ↓
store Raw Artifacts
        ↓
run the Analysis Preparation
        ↓
write the Analysis-ready Artifact
```

最终生成的数据应：

* 语义明确；
* 可重复生成；
* 可以直接交给 AI 分析；
* 可以通过增加 Source Capture 横向扩展；
* 可以在不破坏采集层的情况下调整 Analysis-ready Artifact 内容和输出结构。

---

## 13. 文档维护

* 本文件是 `market-snapshot` 模块的架构层面 authority。
* 本文件遵循渐进式披露原则：只描述理解本模块所必需的核心目标、语义与边界。更具体的数据需求、执行规则和实现细节放在对应的下层文档或 Guide 中，并通过明确引用按需读取。
* 不要要求 Agent 在处理局部任务时默认读取与任务无关的全部 authority。

### 需要更新本文件的变更

* Source / Source Capture / Raw Artifact / Analysis Preparation 的职责边界变化；
* Analysis-ready Artifact 输出组织的所有权变化（谁决定其输出结构）。

### 不需要更新本文件的变更

以下变化由对应的 Guide 承载，不修改本文件：

* 新增一个具体 Source Capture；
* Raw Artifact 具体内容（字段、分类）的变化；
* 具体 Analysis-ready Artifact 的字段清单、文件拆分或输出结构变化；
* 某个实现模块内部的实现调整。

### reconciliation

若实现与本文件不一致，应先在本文件或对应 Guide 完成 reconciliation，或明确记录差异，不得静默选择另一套设计。
