<!-- Approval evidence: user-supplied Goal G1 on 2026-11-03 (Asia/Shanghai).
Original wording below, trailing whitespace normalized. Historical design intent, not a
competing runtime authority. Canonical encoded definition: task.json. This approval
covers Task definition only; it does not authorize live Tushare or Calendar execution. -->

# DSH Goal G1 — Equity Index Futures Basis Monitor Task Authority

## 0. Execution Identity

Repository: `ougachakaaa/hg-market-state-lab`

Branch: `feat/workbench-futures-basis-task`

Required baseline HEAD:

`4149abb53219c4a740449c51facbdf5270620337`

本 Goal 必须在 G0 创建的同一分支上继续执行。

执行前：

1. 确认当前分支与指定 HEAD。
2. 检查 working tree。
3. 不重新创建分支。
4. 不自动合并新的 develop。
5. 不覆盖用户未提交的修改。

本次只执行 G1，不提前进入 G2。

---

## 1. Goal

创建一个正式、版本化、Agent 可发现的 Workbench Task：

`equity_index_futures_basis_monitor`

Version: `1`

目的：

允许 Agent 根据用户指定的股指期货品种和日期范围，调用 Market State Lab 已有的公开数据能力，取得股指期货历史年化升贴水率，并生成机器可读数据与简洁报告。

预期使用方式：

- 查询中证1000最近两周所有股指期货合约的年化贴水率。
- 查询 IF/IH/IC/IM 最近十个交易日的升贴水。
- 查询 IM 在指定历史日期范围内的年化基差。
- 获取查询结果用于后续统计研究或可视化。

本 Goal 只负责 Semantic Decision Encoding、Authority Reconciliation 和 G2 Implementation Readiness。

**不进行代码实现、不调用真实市场数据。**

---

## 2. Authority Discovery

遵循 repository Progressive Disclosure。

首先阅读：

1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. `workbench/AGENTS.md`
4. `workbench/ARCHITECTURE.md`
5. `workbench/contracts/TASK.md`
6. `workbench/contracts/RUN.md`
7. `workbench/contracts/GATE.md`
8. `workbench/tasks/README.md`

随后检查当前 Task Catalog 的组织约定。

业务能力从以下入口进入：

- `data_snapshot/CAPABILITIES.md`
- `data_snapshot/src/data_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md`
- 该产品的 `read-contract.md`
- `data_snapshot/src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md`

仅在需要确认 Source 或数据完整性时进一步阅读对应 specialized authority。

禁止扫描整个 Research、Data Lake 或历史研究成果。

---

## 3. Core Semantic Decisions

### 3.1 Task ownership

Workbench Task 负责：

- 接收和解析用户意图。
- 冻结实际输入。
- 选择已有公开能力。
- 编排多个 family 的查询。
- 生成约定输出。
- 记录 Run、Gate 与证据。

Workbench Task 不拥有：

- 股指期货合约生命周期。
- 年化基差计算公式。
- 期货数据 Source。
- 市场数据完整性定义。
- Dataset 存储。
- Research Statistics 的业务计算。

这些语义应继续由已有 owning modules 负责。

### 3.2 Primary capability

优先复用：

`data_snapshot.products.cffex_equity_index_basis_history`

Public API:

`run_cffex_equity_index_basis_history(request)`

其请求为：

- `futures_family`
- `start_trade_date`
- `end_trade_date`

一个请求只支持一个 family。

多个 family 由 Task 执行层分别调用，不修改 Snapshot Product 原有 scope。

不得重复实现年化公式或另建一个并行的 Basis Calculator。

### 3.3 Supported families

V1 支持：

| Family | Underlying |
|---|---|
| IF | 000300.SH |
| IH | 000016.SH |
| IC | 000905.SH |
| IM | 000852.SH |

Agent 可以将明确的中文指数名称解析成对应 family。

未知或歧义名称不得猜测。

### 3.4 Contract slots

直接继承共享 CFFEX Basis Authority：

`M0 / M1 / Q1 / Q2`

保留每个实际交易日全部符合现有 Product 契约的 active contracts。

不按成交量、主力标记、持仓量或流动性筛选。

不将 slot 重新命名为另一套 M1/M2 体系。

### 3.5 Basis semantics

直接继承已有 formula：

```text
basis_pct =
    (futures_close / underlying_close - 1) * 100

annualized_basis_pct =
    basis_pct * 365 / max(days_to_delist, 1)
```

负值表示贴水，正值表示升水。

该结果是简单线性年化的市场价格差异，不是可实现套利收益率，也不是滚动持有策略收益率。

到期日及近到期合约的年化值可能非常敏感；报告必须标明剩余天数和年化口径。

不修改现有共享 authority。

---

## 4. Input Contract

V1 的核心业务输入：

```json
{
  "futures_families": ["IM"],
  "start_date": "2026-10-20",
  "end_date": "2026-11-03"
}
```

规则：

- `futures_families` 为非空集合。
- 允许 IF/IH/IC/IM 的合法组合。
- 日期两端 inclusive。
- 日期范围必须有效。
- 不允许未来结束日期。
- 不自动扩展或收缩用户指定范围。

### Natural-language resolution

支持以下自然语言表达：

- 最近两周
- 最近十个交易日
- 指定起止日期
- 中证1000
- 所有股指期货

对于“最近两周”：

建议采用截至最近已完成的 CFFEX 交易日、包含该日的连续 14 个自然日区间。

对于“最近 N 个交易日”：

使用已发布的 CFFEX 交易日历确定范围，不能将其替换为 N 个自然日。

所有相对时间在执行前解析为确定的绝对日期。

Run 必须保存：

- 原始请求。
- 解析后的 family 集合。
- 解析后的日期范围。
- 时间解析依据。
- 数据查询范围。

如果没有足够依据确定最近完成的交易日，不得靠猜测继续执行。

---

## 5. Output Contract

每次执行预期生成三个结果文件。

### 5.1 result.json

标准化结果。

必须保留：

- Task ID/version。
- 原始请求与 resolved inputs。
- 每个 family 的查询状态。
- 请求日期范围与实际观测日期范围。
- Source identity。
- 逐合约结果或对明细文件的稳定引用。
- 数据覆盖情况及局限。
- 失败原因与未完成范围。

不能用请求的结束日期冒充实际最后观测日期。

### 5.2 basis_daily.csv

每个实际交易日、每个 family、每个合约一条记录。

最小字段：

```text
trade_date
futures_family
underlying_code
contract_code
contract_slot
delist_date
days_to_delist
underlying_close
futures_close
basis_pct
annualized_basis_pct
```

字段含义继承已有 Snapshot public model。

不添加未经业务确认的金融指标。

### 5.3 REPORT.md

面向人的简洁报告。

应包括：

1. 查询目标与实际日期范围。
2. 最新有效交易日的各 family 四档年化基差。
3. 数据覆盖与失败信息。
4. Source、公式和年化单位。
5. 近到期年化值风险说明。

对于不同 family 的最新观测日期不一致，必须显式展示，不能假装属于同一交易日。

V1 不要求交互图表、统计分布、预测、交易建议或回测。

### Output ownership

Task 输出属于具体 Run。

原始数据和报告应作为 Run artifacts 保存或关联，遵循现有 Workbench storage contract。

不得把 Run evidence 与 Research Publication 混为一体。

不得将大量真实行情文件直接提交 Git。

---

## 6. Failure and Completeness Semantics

现有 Snapshot Product 对单个 family 的不完整 panel 会整体失败。

Task 必须保留这一边界：

- 不删除缺失合约来制造完整结果。
- 不补造价格。
- 不自动更换合约。
- 不使用其他 family 结果替代。
- 不将失败查询解释为零贴水。

对于多个 family：

允许保留已成功 family 的结果，同时明确报告失败 family。

整体成功要求全部请求 family 满足验收标准。

部分成功不得标记为完整 PASS。

尤其需要审查一个问题：

现有 Snapshot Product 的成功只证明其实际观察日期上的完整 panel，不必然证明请求区间内每个预期交易日均已取得。

G1 应明确 Task 的 coverage 表达方式：

- 区分 requested window 与 observed window。
- 不把 Snapshot Product 的成功错误地解释为完整日历覆盖。
- 对最近交易日数据缺失必须显式报告。
- 如需额外交易日校验，优先使用现有公开 Calendar 能力，并保持其语义 ownership。
- 无法验证时标记为 unverified，不作完整性声明。

将此作为 G2 必须满足的关键不变量。

---

## 7. Task Authority Topology

建议创建：

```text
workbench/tasks/
└── equity_index_futures_basis_monitor/
    ├── ARCHITECTURE.md
    ├── task.json
    ├── DESIGN_REQUEST.md
    ├── README.md
    └── authority/
        └── QUERY_AND_RESULT.md
```

职责：

- `ARCHITECTURE.md`：Task identity、ownership、关键不变量与导航。
- `task.json`：正式版本化 Task 定义、允许能力、输入、输出及 Gates。
- `DESIGN_REQUEST.md`：本次批准的设计范围与需求来源。
- `README.md`：Agent 使用路径、当前实现状态及 G2 待实现内容。
- `authority/QUERY_AND_RESULT.md`：具体输入输出、时间解析、完整性及失败契约。

文件组织可以按实际 semantic ownership 微调，但必须遵循 progressive disclosure。

不得为简单 Task 创建大量重复专题文件。

### Task approval

Task 定义批准不等于市场数据执行授权。

`task.json` 必须满足现有 Task Contract 的完整结构。

Approval reference 必须指向真实可追溯的用户授权或设计请求，不能伪造用户批准证据。

本次 G1 授权仅覆盖 Task 定义落地，不授权真实 Tushare 请求。

G2 的实际执行必须遵循独立 execution authorization。

---

## 8. Minimal Gates

不要复制 `historical_return_observation` 的全部历史 Gate。

建议使用三个 Task-owned Gates：

### input_resolution

验证 family、日期、参数及明确的执行意图已正确解析并冻结。

### basis_acquisition

验证通过已有 public Product API 获得真实结果，并记录 Source、实际覆盖与 family-level failures。

### result_delivery

验证 JSON、CSV、Markdown 输出与 Run evidence 一致，且完整性声明有实际依据。

Gate IDs、依赖关系和 PASS/FAIL/BLOCKED 判定必须符合 Workbench 共享 Gate Contract。

G1 只编码定义，不生成虚构 PASS evidence。

---

## 9. G1 Acceptance Criteria

完成 G1 必须满足：

1. Task 已登记到 `workbench/tasks/README.md`。
2. Task version 1 定义合法，approval evidence 可追溯。
3. Agent 能从根 AGENTS.md 逐层找到新 Task。
4. 输入、输出、公式复用和失败边界已明确。
5. 与现有 Snapshot authority 不冲突。
6. 不新增平行基差计算语义。
7. G2 已有明确的 implementation contract。
8. 既有 `historical_return_observation` 完全不受影响。

重点验证：

- JSON 合法性与 Task Contract 必需字段。
- 文档链接和 navigation。
- Authority 引用准确性。
- 最终 diff。

若仅修改 authority，不运行全仓库测试。

不运行真实行情，不安装额外依赖，不启动 Docker 或数据库。

---

## 10. Explicit Non-Goals

G1 不实现：

- Task runtime Python scripts。
- Tushare 数据请求。
- 新 Data Lake Dataset。
- 新 Snapshot Product。
- HTTP endpoint。
- Web UI。
- Generic Task Engine。
- Scheduler。
- 新 Research Case。
- 回测或交易策略。
- 数据缓存重构。

禁止为了未来可能的扩展而设计新的通用框架。

---

## 11. Commit & Final Report

完成后创建独立 commit。

建议：

`docs(workbench): define equity index futures basis monitor task`

Final Report 必须包含：

1. Branch、baseline、final commit。
2. 新增和修改的 authority 文件。
3. Task 的输入输出概要。
4. 复用的 Snapshot public API。
5. Task-owned Gates。
6. 发现并解决的 authority conflicts。
7. 未解决的 semantic gaps。
8. 验收结果。
9. G2 Implementation Ready 判断。

最后明确：

`G1: PASS / PARTIAL / BLOCKED`

`G2 READY: YES / NO`

本轮停止在 Authority Ready，不实施 G2。

执行原则：以最小稳定 authority 支撑后续实现，不重新发明已经存在的业务语义。
