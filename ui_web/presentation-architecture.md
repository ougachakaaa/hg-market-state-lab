# ui_web 内部展示架构 authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，拥有 frontend 内部 presentation architecture 的职责分层、依赖方向、状态边界与共享规则。Application 当前组合哪些 surface 由 [application authority](application.md) 定义；ordinary UI、theme 与 CSS policy 由 [UI system authority](ui-system.md) 定义；generated contract ownership 由 [contract feedback-loop authority](contracts.md) 定义；产品展示与 visualization 语义仍由 [feature catalog](FEATURES.md) 导航到各 feature authority。

## 1. 分层与依赖方向

Frontend 采用独立 vertical slice，并遵循以下职责方向：

```text
Application Shell
        ↓
Feature Page
        ↓
Feature Hooks
       ↙     ↘
Feature API  Feature Model
       ↘     ↙
Feature Components + Feature Charts
        ↓
Shared Presentation Infrastructure
```

Backend facts 的展示数据流进一步约束为：

```text
owning module semantic contract
        ↓
backend HTTP contract / OpenAPI
        ↓
feature API adaptation and validation
        ↓
feature hooks orchestration
        ↓
feature model / projection
        ↓
feature presentation
```

Stable ownership direction 是 `app → feature page → feature hooks → feature API / model → presentation consumers → shared infrastructure`。这不是要求所有 runtime call 都形成单链，而是锁定以下依赖 invariant：

```text
shared     → never depends on a feature
feature A  → never depends on feature B semantic internals
api        → never depends on React presentation
model      → never depends on React lifecycle or hooks
hooks      → may integrate feature API + feature model for React
page       → composes feature-facing React surfaces
```

Application 可以组合 feature public entry；feature internals 可以依赖 `shared`。Sibling features 不通过 application shell 或 `shared` 交换 semantic state、DTO、projection、hook 或 visualization logic。

以下目录表达 canonical ownership zone，不要求每次变更都建立完整目录树，也不授权 authority-only 变更移动现有实现：

```text
ui_web/src/
    app/                    application entry, navigation, layout and composition
    features/<feature>/
        page/               vertical-slice composition root
        api/                generated contracts, request adaptation and validation
        hooks/              React lifecycle and feature-state orchestration
        model/              pure deterministic presentation logic
        components/         feature-specific non-chart UI
        charts/             feature-specific chart semantics and visual encoding
    shared/
        ui/                 domain-neutral UI primitives
        charts/             domain-neutral chart integration
        http/               domain-neutral transport mechanisms
        format/             genuinely invariant generic formatting
```

目录名和 incidental component tree 可以随实现调整，但上述 ownership 与 dependency direction 必须保持。

## Dual Runtime controller / Presentation boundary

上述 HTTP / hooks 数据流属于 Production。Static Demo 从 [已提交 Example](src/demo/EXAMPLES.md) 取得并校验同一正式 Result，经 feature-local static controller 组合相同 Presentation；不经过 HTTP request 或生产 Query/Run Hook。Application composition、Feature Presentation、Production Data/Execution Controller 与 Static Example Controller 必须分离。Runtime 选择不改变产品含义、Result Contract 或 feature ownership。

Production 页面是业务展示的唯一实现来源：Shell、页面结构、结果组件、图表/表格及适用的纯本地 state 共同消费 validated facts。Page 可以保留为生产 composition root，但可复用的展示不得依赖它的在线 controller；static composition 只能消费 feature public Presentation entry。Local state 与 pure projection 仍留在 owning feature，不能复制到 Demo 或提升为跨 feature 业务 state。现有 API 中与 transport 共址的校验允许抽取为 feature-local pure validator，复用 generated contract，而不 import HTTP client。

Shared Shell 展示不拥有认证 lifecycle：由 production composition 将 gate、身份/退出动作与在线页面组合在其外部；静态 composition 提供匿名披露、静态 content 与路由。不得以禁用按钮替代依赖隔离，也不引入 generic Mock Server、plugin 或 DI framework。详细 capability 与 isolation gates 见 [Demo Runtime](src/demo/ARCHITECTURE.md) 和 [实施 handoff](src/demo/IMPLEMENTATION.md)。

## 2. Application Shell 与 Feature Page

Application shell 只拥有：

```text
application entry
navigation
layout / shell
feature composition
production composition authentication state / access gate (outside shared shell presentation)
```

它不拥有 backend product semantics、feature query logic、feature presentation state、financial projection、chart series construction 或 feature-specific formatting。MO Option Chain 与 MO Premium Plane 保持独立 bounded contexts；不得为当前两个 surface 引入 generic plugin framework 或 generalized feature runtime。

Application-level Login / Registration / Logout、身份检查和 Auth request lifecycle 归 [application authority](application.md#5-application-authentication-g3-implemented)；application Auth API/types 与产品 feature API 分开拥有。这里的全局身份状态不是 feature-local server/query state；shared transport 只传递通用信号，不反向依赖 application 或解释产品 state。

Feature Page 是单个 frontend vertical slice 的 composition root。它通过 feature hooks 取得 state 与 actions，并组合 feature controls、components、charts，以及 loading、error、empty、success presentation。Page 应主要表达 presentation composition，不应直接累积大量 HTTP lifecycle mechanics、`AbortController` coordination、stale-response logic、projection algorithms、Plotly trace/layout construction、generic formatting helper 或 domain-neutral reusable UI implementation。

该边界不禁止 Page 使用简单 React hook，也不要求为每个 local boolean 创建独立 hook；可复用或 substantial 的 feature lifecycle / state orchestration 必须进入 `feature/hooks`。

## 3. Feature API、Hooks 与 State Categories

Feature `api/` 拥有 generated OpenAPI / TypeScript contract、transport adaptation 与 runtime response validation。Generated contracts 继续按 `contracts.md` 由 consuming feature 自身拥有；backend DTO 不得移动到 `shared`。

Feature `hooks/` 是 React integration boundary，负责把 React lifecycle 与 interaction 转换为 feature state。它可以拥有：

```text
useState / useReducer
useEffect / useMemo / useCallback / useRef
request and query lifecycle orchestration
cancellation and stale-response coordination
local presentation-state orchestration
composition of API results with pure model functions
```

Feature hooks 可以依赖本 feature 的 `api/`、`model/` 与 generic shared infrastructure，但不得成为 business、projection 或 visualization rule 的第二 semantic owner。

Backend/server state 与 local presentation state 仍是不同 architecture-level ownership category；二者的 React lifecycle / orchestration 主要由 feature hooks 承载：

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

Pure transformations derived from server state 或 presentation state 属于 feature model。Architecture 不依赖 TanStack Query 或任何具体 state-management/query library。

## 4. Feature Model、Components 与 Charts

Feature `model/` 拥有 pure selector、projection、view-model construction、classification、viewport derivation、table/chart projection、presentation-oriented calculation 与 feature-specific deterministic formatting。它把经过验证的 backend facts 转换为 presentation-ready structure，并且必须保持 backend identity、ordering、null/zero/absence 等既有语义，不得发明 feature authority 禁止的 market fact、重新计算 backend-owned financial semantics，或依赖 sibling feature data。

Model 必须在可行范围内脱离 React、JSX、hooks、DOM lifecycle、Plotly renderer lifecycle 与 HTTP request lifecycle，保持可独立测试。它不拥有 `useState`、`useEffect`、`useRef`、request cancellation lifecycle 或 component mounting semantics。

`feature/components` 拥有非 chart 的 feature-specific React presentation，并可以直接组合 Ant Design components；generic library behavior 与 visual design 不改变 feature 对 meaning 的 ownership，也不要求 project-owned wrapper。`shared/ui` 只拥有 domain-neutral reusable UI infrastructure 与 application theme；不得因为两个控件当前结构相似，就把 MO、option-chain、premium-plane、expiry、strike、premium metric 或 product DTO 语义提升为 shared ownership。Ordinary UI、wrapper justification 与 custom CSS exception 进一步遵循 [UI system authority](ui-system.md)。

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

Feature `charts` 拥有 series identity、reference line、axis meaning、trace grouping、feature-specific hover information、visual encoding，以及这些语义对应的 Plotly trace/layout construction。`shared/charts` 只能拥有 React / Plotly integration、responsive rendering、common chart defaults 与 generic chart-frame behavior 等 domain-neutral concern；feature semantic colors 与 analytical classification 不得进入 application UI theme 或由 shared chart infrastructure 重新定义。

Feature hooks 可以选择或协调影响 chart projection 的 presentation state，但不拥有 series identity、axis meaning、reference-line semantics 或 feature-specific visual encoding；这些仍属于 feature model / charts。

[Visualization authority](VISUALIZATION.md) 定义明确有限的跨语言 Layer / View contract；Research Explorer 可以消费 producer 已发布的 Layer，feature 仍拥有具体展示语义，shared 只实现 domain-neutral rendering。这个 contract 不授权 arbitrary chart DSL、计算语言或 plugin runtime，也不要求迁移现有 feature charts。

Plotly 是当前 chart stack。Plotly-specific implementation 不得扩散到 application shell、Feature Page orchestration、feature API 或 ordinary feature component；同时不得仅为隐藏 Plotly 而创建 generic chart DSL。目标是 containment，不是 abstraction for its own sake。Exact Plotly package、version 与 library API usage 属于实现细节。

## 5. Shared Infrastructure

`shared/ui`、`shared/charts`、`shared/http` 与 `shared/format` 只有在行为对多个 feature 确实 invariant 且不携带 domain semantics 时才成立。代码相似本身不是共享依据。`shared/ui` 不得仅为隐藏 Ant Design 而包装每个 generic component；repository 自身具有稳定的 domain-neutral behavior 或 policy 时才建立 abstraction。

以下 ownership 必须留在 owning feature bounded context：

```text
product DTO ownership
feature query identity
feature projection
feature visualization semantics
feature-specific formatting
```

Shared infrastructure 不能成为 application 或 feature authority 之外的第二 semantic owner，也不能通过 generic abstraction 耦合 sibling vertical slices。

Feature-specific hooks 必须留在 owning feature，不得因复用 React mechanism 而进入 shared。只有语义确实 domain-neutral、对多个 feature invariant 的 React / DOM integration mechanism 才可以共享；React reuse 本身不是 shared ownership 的依据，也不要求创建 `shared/hooks` 目录。

## 6. 实现选择边界

本 authority 锁定 ownership boundary、dependency direction、server-state 与 presentation-state category、React hooks integration boundary、Page composition boundary、feature/shared boundary 与 chart containment boundary。[UI system authority](ui-system.md) 进一步锁定 Ant Design / Plotly 职责分工、application theme ownership 与 CSS exception policy。具体 hook 名称、React component tree、state/query library、routing mechanism、library version、component/prop selection、token value、CSS filename/structure 和 incidental filename 仍是实现选择，但这些选择不得违反对应 authority。
