# ui_web 模块架构 authority

本文件定义 `ui_web` 的稳定职责、数据依赖方向与 authority 路由。仓库级定位见 [../ARCHITECTURE.md](../ARCHITECTURE.md)；具体 vertical slice 的 authority 与实现共址于 `src/features/`。

## Module identity

The owning directory is `ui_web/`, an independent npm project without a Python namespace. Inherit the [repository naming rules](../ARCHITECTURE.md#naming-and-transition-authority). Interaction, display behavior, generated wire contracts and co-located feature authority/implementation/tests remain unchanged.

## 1. Purpose

`ui_web` 是数据产品与市场状态结果的展示、交互层，负责：

```text
user interaction
requesting explicit read data
presentation
visualization
```

## 2. Responsibility Boundary

`ui_web` 不拥有 Source、Source Capture、Raw Artifact、Analysis Preparation formula、market modeling 或业务计算语义，也不产生交易判断。

前端只消费 owning module 明确发布的 application/product result 与 `ui_http` HTTP contract。它不得为了绘图重新推导产品身份、contract universe、价格 fallback、业务 completeness 或金融指标。

上述 online 产品消费路径之外，已明确契约化的 offline report 可以渲染 producer 提供的完整通用 Visualization Views；
例如 [R01-A offline delivery](../market_research/descriptive/cases/futures_basis/DELIVERY.md)。ui_web 只拥有渲染及静态资源封装，
其 R01-A standalone reader 入口为 [offline reader](src/offline/futures_basis/ARCHITECTURE.md)。不直接 import Research/business internals、执行研究、获取市场数据或绕过 HTTP authentication；该离线路径不发布新的 HTTP product。

## 3. 数据依赖方向

```text
owning module semantic contract
        ↓
ui_http HTTP contract / OpenAPI
        ↓
generated client types
        ↓
ui_web request adaptation
        ↓
interaction and visualization
```

Owning module Markdown authority 定义业务语义，`ui_http` authority 定义 HTTP transport；published OpenAPI 是 HTTP wire contract 的机器可读表达。前端可以消费生成类型与运行时校验，但不得独立维护一份竞争性的 backend schema。

## 4. Authority Routing

Application entry、认证交互与 gate、feature discovery/navigation 与 composition boundary 由 [application authority](application.md) 拥有；它通过 [frontend feature catalog](FEATURES.md) 导航到各 vertical slice，但不拥有 feature-local 语义。
三大业务区的导航、URL 与布局约束见 [Workspace authority](workspace.md)；阶段范围和验收见 [Workspace work packages](workspace-work-packages.md)。

跨语言 domain-neutral Layer / View / Template contract 由 [Visualization authority](VISUALIZATION.md) 拥有；它不建立新的顶层模块或要求 producer 依赖 UI。
该稳定入口按版本导航到 [V2 date-series contract](VISUALIZATION_V2.md)；V1 与现有 online consumer 的契约不因新版本设计而改变。

Frontend 内部 application、Page、API、React hooks、pure model、component、chart 与 shared infrastructure 的 ownership、依赖方向和状态边界由 [presentation architecture](presentation-architecture.md) 拥有。具体 feature 的产品展示与 visualization 语义仍由 co-located feature authority 拥有。

Ordinary application UI、Ant Design、application-level theme、generic UI composition 与 custom CSS exception boundary 由 [UI system authority](ui-system.md) 拥有。Analytical visualization 仍由 feature semantics 与 Plotly chart boundary 拥有。

Frontend-consumed HTTP products 与 application Auth 的 generated OpenAPI / TypeScript ownership、generation obligation 与 freshness feedback loop 由 [contract feedback-loop authority](contracts.md) 拥有。

MO Option Chain 与 MO Premium Plane 的完整业务 Raw / Context JSON 复制、Clipboard 交互与 CSV / Context JSON 导出由 [Daily Data Copy / Export authority](data-copy-export.md) 拥有；产品特有的 source、response identity 与阅读说明仍归各 feature visualization authority。

### Vertical Slice Authority

`ui_web/src/features/*` 中的 feature authority 只拥有对应 vertical slice 的：

```text
user input and presentation state
display scope
visual encoding
interaction
empty and error presentation
```

正式 frontend vertical slices 及其 canonical authority entry 由 application authority 下游的 `FEATURES.md` 导航。feature entry 会按需分别链接 owning product 与 `ui_http` HTTP authority；普通前端任务无需读取 Source、Raw 或不相关产品文档。

## 5. 维护边界

只有展示层职责、backend contract 消费边界、数据依赖方向或下层 authority routing 变化时更新本文件。Application composition 更新 `application.md`，frontend 内部分层与共享边界更新 `presentation-architecture.md`，ordinary UI system 与 CSS policy 更新 `ui-system.md`，单个 feature 的增删更新 `FEATURES.md`，generated contract feedback loop 更新 `contracts.md`。

Ownership、dependency direction、server-state 与 presentation-state category、React hooks boundary、Page composition、feature/shared boundary、Ant Design / Plotly 职责分工、theme ownership、CSS exception policy 与 chart containment 属于 architecture authority；具体 library version、component/prop selection、token value、incidental component tree、CSS filename、state-management library、字段与 feature visual rule 属于实现或 vertical slice authority。实现选择不得推翻前述 architecture boundary。
