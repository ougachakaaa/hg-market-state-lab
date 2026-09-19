# ARCHITECTURE.md — hg-market-state-lab 顶层架构 authority

本文件定义 `hg-market-state-lab` 的仓库级（top-level）架构 authority。

它只回答理解整个项目所必需的问题：这个 repository 是什么、有哪些顶层模块、各模块的职责边界、模块之间的数据流方向，以及处理某模块任务时下一步应该读哪里。

它**不**承载任何单个模块内部的实现细节、数据契约或计算公式。那些内容放在对应模块自己的 authority 或 Guide 中，按需读取。

---

## 1. 项目定位

`hg-market-state-lab` 是用于**市场状态数据准备、市场状态建模与结果展示**的实验性系统。

它不是一个单一的数据快照（Daily Snapshot）工具。

---

## 2. 顶层模块与职责边界

当前顶层模块：

```text
market-snapshot
market-modeling
web-ui
```

### 2.1 market-snapshot

职责：

> 从外部市场数据 Source 捕捉事实，并按照明确的数据需求进行确定性数据准备，生成 analysis-ready artifacts。

其职责终点是：

```text
Analysis-ready Artifact
```

它不负责：

```text
market-state interpretation
regime classification
probability judgment
trading recommendation
UI presentation
```

详细内部 architecture 不在本文件展开。修改 `market-snapshot` 内部 Source Capture / Preparation / Data Service 等语义时，继续阅读 `market-snapshot/ARCHITECTURE.md`。

### 2.2 market-modeling

职责边界先锁到最小：

> 消费 analysis-ready market artifacts，并负责市场状态建模、状态表达，以及未来明确进入该模块的市场分析逻辑。

当前目录只是 placeholder，无实现。

本文件不设计（也禁止提前创建）：

```text
model framework
state schema
signal system
training framework
backtesting
strategy
```

这些以后出现明确设计需求时，再在 `market-modeling` 自己的 authority 中定义。不要提前创造不存在的模型抽象。

### 2.3 web-ui

职责：

> 展示和交互项目产生的数据产品与市场状态结果。

UI 不拥有：

```text
Source semantics
Capture semantics
market modeling semantics
business calculation authority
```

具体前端 architecture 当前保持 deferred。

---

## 3. 顶层数据流

```text
External Market Sources
        ↓
market-snapshot
        ↓
Analysis-ready Artifacts
        ↓
market-modeling
        ↓
Market-state Outputs
        ↓
web-ui
```

这只表达**系统职责与数据流方向**，不要提前把它定义成强制的 runtime deployment topology 或 package import dependency graph。

`market-snapshot` 的 analysis-ready artifacts 也允许被外部 analyzer 直接消费；`market-modeling` 是仓库内未来主要的 downstream consumer，而不是唯一合法 consumer。

---

## 4. Progressive Disclosure 与导航

authority 层级：

```text
AGENTS.md
    ↓
ARCHITECTURE.md（本文件）
    ↓
market-snapshot/ARCHITECTURE.md
    ↓
market-snapshot/guides/*
```

各层回答的问题：

| 层级 | 回答 |
| --- | --- |
| `AGENTS.md` | 工作规则与默认阅读顺序 |
| `ARCHITECTURE.md`（本文件） | 这个 repository 是什么；有哪些顶层模块；模块职责边界；模块之间的数据流；处理某模块任务下一步读哪里 |
| `market-snapshot/ARCHITECTURE.md` | market-snapshot 是什么；Source / Capture / Preparation / Service 的边界；代码职责分层；Raw / analysis-ready artifact 边界 |
| `market-snapshot/guides/*` | 具体的 Source Capture / Raw Artifact / Preparation / Data Service 契约：字段、窗口、公式、失败条件、输出结构 |

Agent 处理任务时的默认路径：

* 先读本文件，明确任务属于哪个顶层模块及其边界；
* 任务属于 `market-snapshot/` 且涉及其架构、数据语义或职责边界时，再读 `market-snapshot/ARCHITECTURE.md`；
* 只有任务需要具体数据产品时，才继续进入 `market-snapshot/guides/*`。

不要求局部任务默认读取整个 repository 的全部 authority。

---

## 5. 文档维护

### 需要更新本文件的变更

* 顶层模块的增删或职责边界变化；
* 顶层数据流方向变化。

### 不需要更新本文件的变更

* `market-snapshot` 内部 Source / Source Capture / Analysis Preparation / Data Service 的语义变化（属于 `market-snapshot/ARCHITECTURE.md`）；
* 具体数据产品的字段、窗口、公式、失败条件、输出结构变化（属于 `market-snapshot/guides/*`）；
* `market-modeling` / `web-ui` 在各自 authority 出现之前的 placeholder 状态维持，不修改本文件。

### reconciliation

若实现或下层文档与本文件不一致，应先完成 reconciliation 或明确记录差异，不得静默选择另一套设计。
