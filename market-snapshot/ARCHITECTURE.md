# market-snapshot 模块架构 authority

本文件定义 `market-snapshot` 内部稳定的架构术语、职责边界与依赖方向。仓库级定位见 [../ARCHITECTURE.md](../ARCHITECTURE.md)；具体 capability 与产品入口统一从 [CAPABILITIES.md](CAPABILITIES.md) 发现。

## 1. 术语

| 术语 | 含义 |
| --- | --- |
| Data Service | 用户可直接请求的完整数据能力，负责 orchestration |
| Source | 项目外部的数据提供方，定义自身数据事实与 API 语义 |
| Source Capture | 按 Source 语义获取并保存事实数据的组件 |
| Raw Artifact | Source Capture 的持久化输出，保留 Source 事实语义并允许 minimal normalization |
| Analysis Preparation | 按明确数据需求对 Raw Artifact 进行的确定性分析准备 |
| Analysis-ready Artifact | Analysis Preparation 的输出 |
| CLI | Data Service 的用户接口，不是业务架构层 |
| Analyzer | 本模块之外、消费 Analysis-ready Artifact 的分析方 |

`Dataset`、`Snapshot`、`Snapshot Assembly` 和 `Snapshot Definition` 不是通用架构层。它们可以作为具体产品或文件名称存在，但不得替代上述术语。

## 2. Purpose 与职责终点

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

`market-snapshot` 的职责止于结构化、可复现、可分析的数据。分析目标可以驱动数据需求，但市场判断、概率、交易信号、推荐与策略属于外部 Analyzer。

## 3. 核心分层

### Data Service

Data Service 是用户可请求的完整数据能力，负责选择并编排所需 Source Capture 与 Analysis Preparation，再发布产品规定的结果。它不定义 Source API 字段，也不实现 Preparation formula。

Data Service/application request、orchestration、result、semantic failure、CLI 与 canonical persisted output 契约见 [Data Service authority](src/market_snapshot/services/ARCHITECTURE.md)。HTTP inbound delivery 由 [backend-api](../backend-api/ARCHITECTURE.md) 拥有。

### Source

Source 定义外部数据事实与 API 语义，不定义本项目的 Analysis-ready Artifact 结构。

### Source Capture

Source Capture 拥有具体 endpoint 调用、query parameters、Source-domain scope selection、minimal normalization 与 Raw Artifact production。

它可以理解 Source-domain fact，例如产品、交易所、合约生命周期和目标交易日；不得根据下游分析偏好筛选合约或生成市场判断。共享 Capture 身份与 Source fact 语义见 [Capture authority](src/market_snapshot/capture/ARCHITECTURE.md)。

### Raw Artifact

Raw Artifact 是 Source Capture 与 Analysis Preparation 之间的持久化契约。它保留 Source 字段与事实语义，允许为稳定 JSON 表达进行 minimal normalization，但不包含 analyzer-specific interpretation。

### Analysis Preparation

Analysis Preparation 负责确定性的 window selection、join、projection、analysis-oriented rename、restructure 与已明确公式计算：

```text
same Raw Artifact
+ same Preparation Definition
= same output
```

它不得采集 Source，也不得产生市场状态判断或交易结论。

### Analysis-ready Artifact

Analysis-ready Artifact 是 Preparation 输出的通用名称。具体产品可以选择 persisted artifact 或 request-scoped read model；其文件名、字段和发布方式由产品 authority 决定。

### CLI

CLI 只负责解析参数、CLI 层校验、解析 Data Service、调用并呈现结果或错误。它不编排 Capture，也不拥有业务语义。

## 4. 依赖方向

```text
CLI → Data Service

Data Service → Source Capture → Source
Data Service → Analysis Preparation → Raw Artifact

Source Capture produces Raw Artifact
Analysis Preparation consumes Raw Artifact
Analysis Preparation produces Analysis-ready Artifact
```

对 HTTP consumer 的跨模块边界固定为：

```text
market-snapshot product/application service
        ↓
public application boundary
        ↓
backend-api HTTP adapter
```

- Analysis Preparation 不得依赖 Source 或发起采集。
- Source Capture 不得依赖 Preparation 输出结构。
- Data Service 不重新定义 Capture 或 Preparation 语义。
- 共享 Capture capability 不等于共享 goal-scoped Raw Artifact；产品不得读取 sibling product 的 Raw 或最终产物，除非产品 authority 明确规定。
- HTTP adapter 由 `backend-api` 拥有，只能投影 Data Service 或 Preparation 已准备的事实，不反向塑造 domain semantics，也不得重新分类 semantic failure。

## 5. Raw 与 Analysis-ready 的边界

### Minimal normalization

只有同时满足以下条件的转换才属于 Raw 层：

1. 不需要理解 Analyzer 目标；
2. 不创造新的分析语义；
3. 只为稳定表达 Source fact；
4. 对同一 Source fact 确定且可逆或语义等价。

典型允许项包括日期格式统一、表格行转 JSON record、Source scalar 转 JSON scalar。join、窗口、分析命名、派生公式、分组与排序属于 Analysis Preparation。

### 语义规则

- Raw 尽量保留 Source 字段名、单位和缺失状态。
- Preparation Definition 决定 analysis-ready 结构、公式、排序与失败边界。
- Source legitimate null、required input 缺失、数值零与事实缺席不得被静默合并；具体区分由相应产品 authority 定义。
- 不自动换日期、猜测 Source fact、补零或静默删除必需记录。

## 6. 可复现性

给定相同 Raw Artifact 和相同 Preparation Definition，Analysis Preparation 必须产生语义一致的结果，不依赖运行时刻、网络、随机性或本地缓存残留。

Preparation Definition 位于 capability catalog 所链接的产品 specialized authority；实现代码不是 authority。实现与 Definition 不一致时必须显式 reconciliation。

## 7. Authority 分工与维护

```text
ARCHITECTURE.md
    ↓ stable module boundaries
CAPABILITIES.md
    ↓ navigation only
co-located product / shared capability ARCHITECTURE.md
    ↓ bounded-context ownership and routing
specialized business authority
    ↓ fields, formulas, application contracts and failure semantics
implementation
```

本文件只在术语、架构层职责、依赖方向或 Raw/Preparation 所有权变化时更新。新增产品、Source Capture、字段或公式不直接修改本文件，应进入 [CAPABILITIES.md](CAPABILITIES.md) 所指向的 canonical owner；HTTP DTO 进入 `backend-api`，UI 行为进入 `web-ui`。

出现冲突时不得通过上层摘要覆盖下层契约；应确定正确 owner 并完成显式 reconciliation。

## 8. Canonical Python Namespace

本模块的 canonical Python package namespace 是：

```text
market_snapshot
```

`market-snapshot` 是通用 market data preparation / market snapshot bounded context；daily cadence 不是 module-level invariant。Daily observations、request-scoped products、intraday observations 与其他 snapshot products 均可位于 `market_snapshot` namespace 下。

实现统一位于 `src/market_snapshot/`，Python import 使用 `market_snapshot`。语义仍然是 daily snapshot 的 `Daily Market Snapshot` 产品，以及 `daily bar`、daily Capture、Source field 与 trade-date 术语，均不因 package namespace 决定而改名。
