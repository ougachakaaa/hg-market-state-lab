# web-ui 内部展示架构 authority

本文档从属于 [web-ui architecture](ARCHITECTURE.md)，拥有 frontend 内部 presentation architecture 的职责分层、依赖方向、状态边界与共享规则。Application 当前组合哪些 surface 由 [application authority](application.md) 定义；generated contract ownership 由 [contract feedback-loop authority](contracts.md) 定义；产品展示与 visualization 语义仍由 [feature catalog](FEATURES.md) 导航到各 feature authority。

## 1. 分层与依赖方向

Frontend 采用独立 vertical slice，并遵循以下职责方向：

```text
Application Shell
        ↓
Feature Page
        ↓
Feature API / State / Model
        ↓
Feature Components + Feature Charts
        ↓
Shared Presentation Infrastructure
```

Backend facts 的展示数据流进一步约束为：

```text
owning module semantic contract
        ↓
backend-api HTTP contract / OpenAPI
        ↓
feature API adaptation and validation
        ↓
feature state / model / projection
        ↓
feature presentation
```

Allowed dependency direction 是 `app → feature page → feature internals → shared infrastructure`。Application 可以组合 feature public entry；feature 可以依赖 `shared`；`shared` 不得依赖任何 feature。Sibling features 不相互依赖，也不通过 application shell 或 `shared` 交换 semantic state、DTO、projection 或 visualization logic。

以下目录表达 canonical ownership zone，不要求每次变更都建立完整目录树，也不授权 authority-only 变更移动现有实现：

```text
web-ui/src/
    app/                    application entry, navigation, layout and composition
    features/<feature>/
        page/               vertical-slice composition root
        api/                generated contracts, request adaptation and validation
        model/              server state, presentation state and projections
        components/         feature-specific non-chart UI
        charts/             feature-specific chart semantics and visual encoding
    shared/
        ui/                 domain-neutral UI primitives
        charts/             domain-neutral chart integration
        http/               domain-neutral transport mechanisms
        format/             genuinely invariant generic formatting
```

目录名和 incidental component tree 可以随实现调整，但上述 ownership 与 dependency direction 必须保持。

## 2. Application Shell 与 Feature Page

Application shell 只拥有：

```text
application entry
navigation
layout / shell
feature composition
```

它不拥有 backend product semantics、feature query logic、feature presentation state、financial projection、chart series construction 或 feature-specific formatting。MO Option Chain 与 MO Premium Plane 保持独立 bounded contexts；不得为当前两个 surface 引入 generic plugin framework 或 generalized feature runtime。

Feature Page 是单个 frontend vertical slice 的 composition root。它可以协调 query/model state，并组合 feature controls、components、charts，以及 loading、error、empty presentation。Page 应主要表达 presentation composition，不应直接累积大量 HTTP lifecycle mechanics、runtime response validation、projection algorithms、Plotly trace/layout construction、generic formatting helper 或 domain-neutral reusable UI implementation。

## 3. Feature API、Server State 与 Presentation State

Feature `api/` 拥有 generated OpenAPI / TypeScript contract、transport adaptation 与 runtime response validation。Generated contracts 继续按 `contracts.md` 由 consuming feature 自身拥有；backend DTO 不得移动到 `shared`。

Feature `model/` 拥有 query/server-state lifecycle、local presentation state 及 presentation projection。Backend/server state 与 local presentation state 是不同 ownership category：

```text
server/query state                 presentation state
-------------------------------    -------------------------------
query identity                     selected expiry
loading / success / failure        visible series
cancellation                       Call / Put selection
stale-response prevention          metric selection
validated backend result           viewport and display colors
backend response lifecycle         other local visualization controls
```

Presentation state 只控制已取得 facts 的本地展示。改变 presentation state 不得隐式改变 HTTP query identity、触发 backend recomputation 或成为 transport parameter，除非 owning feature authority 明确将其定义为 query input。

Server-state 与 presentation-state mechanism 可以由 feature-local hook 或其他实现承载。Architecture 不依赖 TanStack Query 或任何具体 state-management/query library。

## 4. Feature Model、Components 与 Charts

Feature model / projection 把经过验证的 backend facts 转换为 presentation-ready structure，例如 selected-expiry、table、chart projection，viewport derivation、display classification 与 presentation-oriented formatting。Projection 必须保持 backend identity、ordering、null/zero/absence 等既有语义，不得发明 feature authority 禁止的 market fact、重新计算 backend-owned financial semantics，或依赖 sibling feature data。可以保持为 pure logic 时，不得引入 React rendering concern 或 Plotly rendering detail。

`feature/components` 拥有非 chart 的 feature-specific React presentation。`shared/ui` 只拥有 domain-neutral reusable UI infrastructure；不得因为两个控件当前结构相似，就把 MO、option-chain、premium-plane、expiry、strike、premium metric 或 product DTO 语义提升为 shared ownership。

Chart 数据流固定为：

```text
backend facts
        ↓
feature projection
        ↓
feature chart semantics
        ↓
shared chart infrastructure
        ↓
Plotly rendering
```

Feature `charts` 拥有 series identity、reference line、axis meaning、trace grouping、feature-specific hover information、visual encoding，以及这些语义对应的 Plotly trace/layout construction。`shared/charts` 只能拥有 React / Plotly integration、responsive rendering、common chart defaults、shared visual theme 与 generic chart-frame behavior 等 domain-neutral concern。

Plotly 是当前 chart stack。Plotly-specific implementation 不得扩散到 application shell、Feature Page orchestration、feature API 或 ordinary feature component；同时不得仅为隐藏 Plotly 而创建 generic chart DSL。目标是 containment，不是 abstraction for its own sake。Exact Plotly package、version 与 library API usage 属于实现细节。

## 5. Shared Infrastructure

`shared/ui`、`shared/charts`、`shared/http` 与 `shared/format` 只有在行为对多个 feature 确实 invariant 且不携带 domain semantics 时才成立。代码相似本身不是共享依据。

以下 ownership 必须留在 owning feature bounded context：

```text
product DTO ownership
feature query identity
feature projection
feature visualization semantics
feature-specific formatting
```

Shared infrastructure 不能成为 application 或 feature authority 之外的第二 semantic owner，也不能通过 generic abstraction 耦合 sibling vertical slices。

## 6. 实现选择边界

本 authority 锁定 ownership boundary、dependency direction、server-state 与 presentation-state category、Page composition boundary、feature/shared boundary 与 chart containment boundary。具体 React component tree、state/query library、routing mechanism、CSS structure、Plotly package/version 和 incidental filename 仍是实现选择，但这些选择不得违反本 authority。
