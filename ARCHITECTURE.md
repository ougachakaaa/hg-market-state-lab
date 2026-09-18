# ARCHITECTURE.md — Daily Market Snapshot Phase 1 Architecture

本文件定义 `daily-market-snapshot` 在 Phase 1 的架构层面 authority。

它只描述理解本项目所必需的核心目标、语义与边界。具体的数据需求、执行规则和实现细节放在对应的下层文档或 Guide 中（见第 8 节与第 13 节），按需读取。

---

## 0. 术语

全文固定使用以下术语，不做同义替换：

| 术语 | 含义 |
| --- | --- |
| Source | 外部数据来源 |
| Dataset | 从某个 Source 获取的一组具有明确语义的数据 |
| Raw Dataset | Dataset 落地后的事实文件 |
| Snapshot | 为特定分析需求组织出来的每日数据产品 |
| Snapshot Definition | 当前生效的 Snapshot 组织方式 |
| Snapshot Assembly | 从 Raw Dataset 组装出 Snapshot 的过程 |

---

## 1. Purpose

`daily-market-snapshot` 用于从金融市场数据源获取数据，并生成结构清晰、可复现、适合后续 AI 分析的每日市场快照。

第一阶段目标是建立最小可运行闭环：

```text
Data Source
    ↓
Data Collection
    ↓
Raw Dataset
    ↓
Snapshot Assembly
    ↓
Daily Snapshot Files
    ↓
AI Analysis
```

本阶段重点不是建设通用数据平台，而是建立简单、明确、容易扩展的数据边界。

### 1.1 Responsibility Boundary

本项目的职责止于产生结构化、可复现、可分析（analysis-ready）的市场数据（Source → Raw Dataset → Snapshot / data output）。第 1 节流程图中最后一步 "AI Analysis" 属于外部 analyzer，不属于本项目。

业务分析及其规则（例如价格中枢、噪声区、期权反向交易候选区域、bullish / bearish 判断、交易信号、目标点位等结论）属于外部 analyzer，不进入本项目的数据契约，也不得作为本项目 Snapshot Assembly 的业务逻辑实现。

分析目标可以作为数据需求（Dataset / output definition）的来源，驱动本项目确定"需要哪些数据"；但分析规则与结论不由本项目定义或执行。

---

## 2. Core Architecture

第一阶段只定义三个核心概念：

```text
Source → Dataset → Snapshot
```

### Source

外部数据来源。

例如：

* Tushare

Source 负责提供数据，不定义最终 Snapshot 的组织形式。

### Dataset

从某个 Source 获取的一组具有明确语义的数据。

例如：

* 指数日行情
* 每日估值
* 资金流
* 融资融券数据

Dataset 是数据采集层与 Snapshot 组织层之间的主要边界。

不同 Dataset 应尽量能够独立采集和保存。

### Snapshot

为特定分析需求组织出来的每日数据产品。

Snapshot 可以：

* 组合多个 Dataset；
* 选择 Dataset 中需要的字段；
* 调整数据层级；
* 增加新的分析主题；
* 拆分成多个文件；
* 修改最终输出格式。

Snapshot 的组织方式允许随着分析需求演进。

### 依赖方向

三层之间的依赖方向是单向的：

```text
Source ← Dataset ← Snapshot
```

* Snapshot 依赖 Dataset，Dataset 依赖 Source。
* Dataset 不得依赖 Snapshot 的组织方式。
* 采集层不得因为 Snapshot 的输出结构调整而改变。

---

## 3. Raw Data and Snapshot Boundary

项目必须明确区分：

```text
Raw Dataset
```

和：

```text
Snapshot
```

### Raw Dataset

Raw Dataset 表示从数据源获取的数据事实。

主要职责是：

```text
Source
    ↓
API Call
    ↓
minimal normalization
    ↓
Raw Dataset File
```

Raw 层应尽量避免包含针对某个具体 Snapshot 的组织逻辑。

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

判断标准：若某项处理需要知道"这个 Snapshot 要用它做什么"，则它属于 Snapshot Assembly，不属于采集层。

### Snapshot

Snapshot 是 Raw Dataset 的下游组织结果：

```text
Raw Dataset A
Raw Dataset B
Raw Dataset C
      ↓
Snapshot Assembly
      ↓
Daily Snapshot
```

Snapshot 可以频繁调整，而不要求重新设计数据采集层。

### 语义规则

* 原始数据不做分析层解读。
* Snapshot 只能包含 Raw Dataset 的下游组织结果，不得包含只存在于 Snapshot 中且无法回溯到 Raw Dataset 的数据事实。

因此：

> 数据采集负责获得事实，Snapshot Assembly 负责按照当前分析需求组织事实。

这是第一阶段最重要的架构边界。

---

## 4. 架构边界的执行

架构边界在运行时的直接推论：

* Snapshot Assembly 只从本地 Raw Dataset 组装，不得在组装阶段直接发起采集。
* 采集与组装的具体写入、覆盖、重跑与失败处理属于实现策略，不由本文件预设；需要时由对应 Guide 明确。

---

## 5. Extensibility Model

项目需要支持分析需求不断扩展，但第一阶段不引入插件框架、复杂抽象或通用 Pipeline 系统。

横向扩展采用最简单的方式。

### 增加新的数据内容

当分析需要新的市场数据时：

```text
Identify required Dataset
    ↓
Add data collection script
    ↓
Generate Raw Dataset
    ↓
Include Dataset in Snapshot if needed
```

新增 Dataset 不应要求重构已有 Dataset。

### 调整 Snapshot 内容

如果新的分析需要：

* 增加字段；
* 删除字段；
* 增加 Dataset；
* 改变分类方式；

主要修改 Snapshot Assembly 和相关 Guide。

Raw Dataset 不应因为单纯的输出结构调整而改变。

### 调整 Snapshot 输出格式

Snapshot 可以从：

```text
snapshot.json
```

演进为：

```text
YYYY-MM-DD/
    market.json
    liquidity.json
    breadth.json
    metadata.json
```

或其他更适合分析的组织方式。

Snapshot 输出结构不是项目长期固定 API。

---

## 6. Reproducibility

虽然 Snapshot 的定义允许演进，但同一个已经确定的 Snapshot 定义应该能够稳定重复执行。

即：

```text
Snapshot Definition A
        ↓
2026-09-15
2026-09-16
2026-09-17
```

应该产生语义一致的数据结构。

当分析需求发生变化时，可以形成新的 Snapshot Definition。

因此项目追求的不是：

> 永久固定的 Snapshot Schema。

而是：

> 对当前已经确定的数据需求，能够稳定、明确、可复现地生成 Snapshot。

### Snapshot Definition 的 authority 落点

Snapshot Definition 的 authority 是 `guides/` 中对应的 Guide（当前为 `guides/daily-market-snapshot.md`）。

`scripts/build_snapshot.py` 只是该 Definition 的实现：它按照 Guide 读取 Raw Dataset 并组装 Snapshot，不构成 authority，不得反向定义或修改 Snapshot Definition。实现与 Guide 不一致时，必须对实现做 reconciliation，不得静默改变语义。

本阶段**不**引入额外的 schema 定义文件、Snapshot 注册表或版本管理框架。

### 可复现性要求

Snapshot 的结果只依赖该交易日的 Raw Dataset 与当前 Snapshot Definition。

不得依赖运行时刻、网络状态、随机性或本地缓存残留。

---

## 7. Agent-oriented Workflow

本项目允许 Agent 参与数据需求实现和 Snapshot 组织。

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
Implement required Dataset / Snapshot change
      ↓
Run and verify
```

Agent 可以承担：

* 根据数据需求识别需要的 Dataset；
* 添加新的数据采集脚本；
* 调整 Snapshot Assembly；
* 调整输出结构；
* 增加必要测试；
* 更新相关 Guide。

但是 Agent 不应自行改变已经确定的业务语义。

已经确定的业务语义包括：

* Dataset 的含义与职责；
* Snapshot 的内容定义；
* 输出的语义；
* 采集层与 Snapshot 层之间的职责边界。

上述变更必须先更新 authority（本文件或对应 Guide），再修改实现。

---

## 8. Guide Responsibility

`guides/` 用于描述具体的数据需求和可执行 workflow。

Guide 可以说明：

* 当前 Snapshot 需要哪些数据；
* Dataset 对应什么数据源；
* Snapshot 如何组织这些 Dataset；
* 如何运行采集；
* 如何生成 Snapshot；
* 如何检查结果。

Guide 是 Agent 执行具体任务时的重要上下文。

架构 authority 定义稳定边界。

Guide 定义当前任务和当前 Snapshot 的具体需求。

两者职责不同：

| | authority（本文件） | Guide（`guides/`） |
| --- | --- | --- |
| 定义 | 稳定边界与核心语义 | 当前任务与当前 Snapshot 的具体需求 |
| 变化频率 | 低 | 随分析需求变化 |
| 内容 | Source / Dataset / Snapshot 的职责与分层规则 | 需要哪些数据、如何采集、如何组装、如何检查 |
| 优先级 | 冲突时以本文件为准 | 不得与本文件冲突 |

约束：

* Guide 不得与 authority 冲突，也不得引入新的架构概念。
* 出现冲突时以 `ARCHITECTURE.md` 为准。

---

## 9. Initial Project Structure

第一阶段保持简单：

```text
daily-market-snapshot/

├─ AGENTS.md
├─ ARCHITECTURE.md
├─ README.md
├─ pyproject.toml
│
├─ guides/
│   └─ ...
│
├─ config/
│   └─ ...
│
├─ scripts/
│   ├─ fetch_*.py
│   └─ build_snapshot.py
│
├─ data/
│   ├─ raw/
│   └─ snapshots/
│
└─ tests/
```

具体脚本名称和 Snapshot 文件结构由实际数据需求决定。本文件不预设任何具体 Dataset、脚本名或 Snapshot 文件结构；这些由对应的 Guide 固化。

约定的目录职责：

* `guides/`：描述具体数据需求与可执行 workflow。
* `config/`：非敏感的运行配置。凭据（例如 `TUSHARE_TOKEN`）只从环境变量读取，不进 `config/`，不进版本控制。
* `scripts/`：`fetch_*.py` 负责采集单个 Dataset 并写出 Raw Dataset；`build_snapshot.py` 负责 Snapshot Assembly。
* `data/raw/`：Raw Dataset 输出目录。
* `data/snapshots/`：Snapshot 输出目录。
* `tests/`：与 `scripts/` 对应的测试。

`data/raw/` 与 `data/snapshots/` 是运行产物，不进入版本控制。

---

## 10. Phase 1 Non-goals

第一阶段不主动建设：

* 数据库；
* 实时行情系统；
* 分布式采集；
* 通用工作流引擎；
* Dataset 插件系统；
* DataSource 基类体系；
* Pipeline framework；
* Dataset registry；
* 复杂 Schema version framework；
* 通用 ETL 平台。

同时，以下内容也不属于第一阶段范围：

* 采集层与 Snapshot 层之间的通用参数化配置层；
* 跨 Dataset 的原始数据重试、缓存或版本化策略；
* 采集层的调度、增量更新与自动化编排。

只有当实际需求产生足够复杂度时，才重新评估是否需要这些能力。

---

## 11. Design Principles

第一阶段遵循以下原则：

### Keep it simple

优先选择能够完成当前需求的最直接实现。

### Semantics before implementation

涉及 Dataset 含义、Snapshot 内容、输出结构和职责边界时，先明确设计，再修改实现。

### Authority before code

已经落入项目 authority 的设计优先于一般工程惯例。

如果代码与 authority 不一致，应明确进行 reconciliation，而不是静默改变语义。

### Stable boundaries, flexible content

Source、Dataset、Snapshot 三层边界应保持清晰。

具体 Dataset 数量、Snapshot 内容和输出结构允许持续变化。

### Agent-friendly

项目结构、Guide 和脚本应保持足够直接，使 Agent 能够通过阅读有限上下文理解并修改项目。

不要为了扩展性提前增加会扩大 Agent 理解成本的抽象。

---

## 12. Phase 1 Success Criterion

第一阶段完成时，应能够：

```text
given a trading date
        ↓
collect required datasets
        ↓
store raw data
        ↓
assemble the current snapshot definition
        ↓
write local snapshot files
```

最终生成的数据应：

* 语义明确；
* 可重复生成；
* 可以直接交给 AI 分析；
* 可以通过增加 Dataset 横向扩展；
* 可以在不破坏采集层的情况下调整 Snapshot 内容和输出结构。

---

## 13. 文档维护

* 本文件是项目架构层面的 authority。
* 本文件遵循渐进式披露原则：只描述理解项目所必需的核心目标、语义与边界。更具体的数据需求、执行规则和实现细节放在对应的下层文档或 Guide 中，并通过明确引用按需读取。
* 不要要求 Agent 在处理局部任务时默认读取与任务无关的全部 authority。

### 需要更新本文件的变更

* Source / Dataset / Snapshot 的职责边界变化；
* Snapshot 输出组织的所有权变化（谁决定 Snapshot 的输出结构）。

### 不需要更新本文件的变更

以下变化由对应的 Guide 承载，不修改本文件：

* 新增一个具体 Dataset；
* Dataset 具体内容（字段、分类）的变化；
* 具体 Snapshot 的字段清单、文件拆分或输出结构变化；
* 某个脚本内部的实现调整。

### reconciliation

若实现与本文件不一致，应先在本文件或对应 Guide 完成 reconciliation，或明确记录差异，不得静默选择另一套设计。
