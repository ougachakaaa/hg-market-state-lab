# ARCHITECTURE.md — web-ui 模块架构 authority

本文件定义 `web-ui` 模块的架构层面 authority。

它只描述理解本模块所必需的核心目标、语义与边界。具体的垂直 slice 用户体验 / visualization contract 放在 `web-ui/guides/*` 中，按需读取。

本模块在仓库顶层的定位、职责边界与数据流见根 `ARCHITECTURE.md`。本文件只负责 `web-ui` 内部的稳定边界。

---

## 1. Purpose

`web-ui` 负责：

```text
user interaction
requesting explicit read data
presentation
visualization
```

它是 project 数据产品与市场状态结果的**展示与交互层**，不重新定义或重新计算业务数据。

## 2. Responsibility Boundary

`web-ui` 不拥有：

```text
Source semantics
Source Capture
Raw Artifact semantics
Analysis Preparation formulas
market modeling semantics
business calculation authority
trading judgment
```

`web-ui` 只消费已经准备好的、可读的市场数据，并把它呈现为人类可读的可视化。

## 3. 数据依赖方向

核心依赖方向：

```text
prepared/readable market data
        ↓
web-ui
        ↓
human-readable visualization
```

前端不得为了绘图重新发明金融数据语义，也不得重新计算后端 authority 已拥有的业务派生逻辑。

独立的 `web-ui/` frontend project 使用 Vite + React + TypeScript；当前已实现 MO option-chain 的日期输入、HTTP 读取和可读结果展示，散点图留待后续阶段。具体 dev 命令与 proxy 地址见根 `README.md` / `DEVELOPMENT.md`。component / state-management 选择不在本文件定义。

## 4. 数据来源边界

前端需要的数据必须来自明确的 backend / read contract；`web-ui` 不直接理解 Source 或 Raw Artifact。

MO option-chain visualization 的数据来源边界已锁定：

```text
web-ui
    ↓ consumes
MO Option Chain read contract
（market-snapshot/guides/mo-option-chain-read-contract.md）
```

`web-ui` 不直接消费：

```text
csi1000-5d-analysis snapshot.json
Raw Artifact
Tushare Source
```

具体 read contract 的 query identity、字段、分组、排序、价格语义与失败语义由 `market-snapshot/guides/mo-option-chain-read-contract.md` 拥有；产品 identity（`MO → 000852.SH`）与 invariants 见 `market-snapshot/guides/mo-option-chain.md`。`web-ui` 只消费该 read contract，不重新定义或重新推导其业务语义。

## 5. Guide Responsibility

`web-ui/guides/*` 定义具体 Web vertical slice 的用户体验 / visualization contract。

architecture 与 Guide 分工：

| | 本文件 | Guide（`web-ui/guides/`） |
| --- | --- | --- |
| 定义 | 稳定边界与依赖方向 | 具体 vertical slice 的输入、展示范围、可视化语义、空/错误语义 |
| 变化频率 | 低 | 随 vertical slice 需求变化 |
| 优先级 | 冲突时以本文件为准 | 不得与本文件冲突 |

当前第一个 vertical slice 的 Guide 是：

```text
web-ui/guides/mo-option-chain-visualization.md
```

## 6. 文档维护

* 本文件是 `web-ui` 模块的架构层面 authority。
* 本文件遵循渐进式披露原则：只描述理解本模块所必需的核心目标、语义与边界。更具体的用户体验 / visualization contract 放在对应 Guide 中，按需读取。

### 需要更新本文件的变更

* `web-ui` 的职责边界或依赖方向变化。

### 不需要更新本文件的变更

* 某个 vertical slice 的具体输入、展示范围、图表字段、空/错误语义变化（属于 `web-ui/guides/*`）；
* framework 的版本、component / state-management 选择及开发配置细节（实现细节，不进入本文件）。

### reconciliation

若实现或下层文档与本文件不一致，应先完成 reconciliation 或明确记录差异，不得静默选择另一套设计。
