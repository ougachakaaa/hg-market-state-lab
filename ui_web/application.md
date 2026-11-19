# ui_web application integration authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，并遵循 [presentation architecture](presentation-architecture.md) 定义的内部 ownership boundary；它只拥有 Web application 的 entry、feature discovery/navigation、layout/shell 与 composition boundary。Ordinary UI、application-level theme 与 CSS policy 遵循 [UI system authority](ui-system.md)。正式 frontend surfaces 由 [feature catalog](FEATURES.md) 导航；各 surface 的产品与 visualization 语义仍由其 co-located feature authority 拥有。

## Dual Runtime composition

Production 与 Static Demo 共用正式 Shell、导航和 feature Presentation；application composition 分别选择 Production Online access/HTTP controllers 与 anonymous static Bundle controllers (DDB-04)。Shared Shell 的展示边界不依赖 Auth、在线 Page 或业务请求 Hook；身份/退出动作、路由和 feature content 由 composition 提供。Production Online 入口支持本机匿名和认证模式，仅该入口 mount 在线 controller。Demo 细节进入 [Demo authority](demo/ARCHITECTURE.md)，其 feature Presentation 仍由正式 feature 拥有；不得复制 Demo 业务页面。本文中的登录、请求、preflight、Run lifecycle 均描述 Production；静态 runtime 不模拟这些状态。

The sole static composition lives in demo/runtime. Formal FastAPI HTTP business results require Bundle admission before static display. Controlled synthetic fixtures belong only to tests. Demo Build requires the real admitted dataset; publication integration belongs to DDB-05.

## 1. Application Surfaces

Production Web application 以 canonical Graph 的首个 Strategy 为登录后默认入口，包含四个一级业务区：

```text
Strategy → Canonical Graph 中的各个 Strategy
Daily Data → MO Option Chain / MO Premium Plane / Futures Calendar Spread（已实现）
Research → Research Catalog & Workspace / Research Explorer（已实现）；Futures Basis Online Research / Calendar Spread Historical Relative Value（已实现 Web Consumer）
Backtesting → Backtesting Overview / Futures Roll Long（WP7 Web Consumer 已实现）
```

进入在线 Workspace 后默认进入首个策略的 `/roadmap/:strategyId`，不提供独立宣传首页。既有在线 feature 保持可访问且相互独立。Research Overview 是面向用户的 Research Study 导览，展示研究目的与独立 Web 页面的完成状态；不以 Capability readiness 推断完成状态。Research Explorer 是辅助成果浏览工具，保留正式路由，通过已知 URL 与浏览器历史访问，不作为 Study 或侧栏项目。Capability 发现继续由原 controller 与 validator 拥有。Futures Basis Online Research 已完成 WP8-B Web Consumer，并复用在线和离线共享 Reader。导航和 URL 由 [Workspace authority](workspace.md) 细化。

## 2. Application Ownership

Application shell 只拥有：

```text
application entry
feature discovery and navigation
application layout / shell
feature composition boundary
online access composition state and gate (outside shared shell presentation)
production login / registration / logout interaction
```

它不拥有或解释：

```text
market or product semantics
product query identity or request adaptation
option or premium calculations
expiry, strike or metric semantics
visual encoding and formatting
feature-local loading, failure or presentation state
```

Application navigation 只选择当前 feature surface，不成为 backend product contract 或 feature-local state 的 semantic owner。

Production Workspace also owns the most recently visited Run route identities and
navigation parameters, within the online Workspace lifecycle defined by
[Workspace Run navigation identity](workspace.md#production-run-navigation-identity).
Navigation memory stores URL identity only. Production composition also owns the
first-visited Backtesting Activity instance and visibility, destroyed with Workspace.
The retained feature continues to own all its data and presentation state.
Features retain ownership of Run lifecycle,
GET/POST, validation, polling, cancellation and result presentation; Application
neither interprets Run status/results nor caches feature DTOs or presentation state.
Navigation memory ends with the online Workspace, even though the outer
authentication gate and history adapter may remain mounted.

## 3. Feature Independence

MO Option Chain、MO Premium Plane、Research Catalog、Research Explorer、Futures Basis Research 与 Backtesting 保持独立 frontend bounded contexts。它们不共享产品 identity、backend DTO、query state、presentation state 或 visualization semantics，也不从 sibling feature 的 response 或 local state 派生自己的事实。

Application composition 不改变各 feature 的 backend dependencies，也不表示 backend products 存在业务耦合。切换 surface 时 feature state 的 React lifecycle 或持久化机制属于实现细节；无论采用何种机制，一个 feature 都不得读取、覆盖或重新解释另一个 feature 的 local state。

## 4. Implementation Boundary

本 authority 不规定 router library、精确 component/props、component tree、mounting strategy、CSS filename 或 state-management library；实现选择遵循 `ui-system.md` 和 [Workspace authority](workspace.md)，不得为未来 feature 引入 plugin 或 generic runtime。

## 5. Application Authentication (G3 implemented)

认证 HTTP、用户状态、审批、Cookie、限流与同源协议唯一归 [Authentication MVP V1](../ui_http/AUTHENTICATION.md)。本节只拥有 application 交互和 gate；G3 已实现下述交互，G4 已完成本地跨层验收。

Login / Registration 是 application-level 入口；普通登录进入默认策略的 `/roadmap/:strategyId`，直接访问已知深层页面且认证成功时保留该页面。用户可切换 Research Catalog、Research Explorer 和两个 MO feature；Futures Basis Research 已实现 Web Consumer。登录状态不属于各 feature 的 local query/presentation state，不经 sibling feature 共享；shell 不因此接管产品 query、DTO 或图表语义。

同一 Workspace 请求生命周期内，已取消的 feature 请求若仍返回 401，也必须关闭当前 gate。已关闭的旧生命周期不得影响后续打开的 Workspace。

Application 管理以下状态及行为：

- 启动或重载时先查询 `/auth/mode`。探测期间保留当前 URL 并暂缓 mount 业务；探测失败显示可重试错误。
- Local 初始化业务请求生命周期并恢复路由，直接打开同一个 Workspace。Header 显示「本地模式」，跳过 `/auth/me`，隐藏账号操作。
- `loopback-http` 和 `production` 均以 `"authenticated"` 进入同一 Web 会话流程。应用继续检查 `/auth/me`，成功时恢复身份，401 时进入登录入口，其他故障显示可重试错误。
- Anonymous 显示 username/password 登录和注册入口。注册 202 只显示通用“申请已受理，等待 Operator 审批后登录”，不获取用户 ID、不判断是否重复、不自动登录或轮询审批。Operator 从服务器 `lab auth` 处理；无 Web admin surface。
- 登录成功依据最小 user identity 开放 gate；失败保留通用 credentials 错误，不能根据 401 猜测账号是否存在、pending 或 rejected。400、403、429（含 Retry-After）、500 有各自可理解的反馈。
- 认证模式的受保护业务/me 请求 401 使 application 返回登录 gate，停止新业务请求、中止/隔离旧请求并清除本客户端已显示的身份/业务结果；stale success 不得恢复登录或旧结果。403 来源拒绝、429 或产品业务错误不自动清除登录状态。
- Local 的意外业务 401 关闭同一请求生命周期，隔离旧请求并显示可重试的本地访问异常。重试重新探测模式。
- Logout 发同源 POST，pending 期间阻止新业务请求并中止/隔离旧请求。204 后清除本地身份与产品结果并回到匿名入口；失败时保留可重试的退出状态，不声称服务端已清 Cookie。过期或缺失 Cookie 的 logout 仍可正常完成。

认证模式的身份来自服务端，浏览器通过 HttpOnly Cookie 管理 JWT。应用请求使用相对同源 URL 和 Cookie credentials。会话续期随服务端成功响应进行，应用依靠登录和 `/auth/me` 的响应恢复身份。前端禁止处理或保存 JWT，也不发起后台续期、会话心跳或 401 刷新。

Auth request adaptation、generated schema/types 及 React lifecycle 属于 application 的 Auth concern（可放在 `src/app/auth/`，incidental filenames 由实现决定），独立于产品 DTO。Domain-neutral `shared/http` 可以传递 401/credentials 信号，但不能依赖 app/feature 或解释产品 state；由 application 显式组合 callback/context。不得为了全局 gate 引入通用 feature runtime。

本地 Vite proxy 为 `/auth` 和业务路径保留浏览器 Host、来源头及 Set-Cookie。浏览器使用 frontend origin。后端 AccessGate 执行 Local 的本机约束与认证模式的 Cookie 和来源检查，具体规则及无状态 logout 语义见 Auth authority。

## Backtesting overview composition

The application composes a transport-free Backtesting overview at `/backtesting` and
mounts the existing execution Page only at `/backtesting/futures-roll-long`. Shared
Shell and overview Presentation support static composition. The static Shell harness
verifies both identities; official Bundle composition uses the admitted Demo runtime.

The shared workspace header remains visible while Content scrolls. Its right edge always exposes a GitHub source link to https://github.com/ougachakaaa/hg-market-state-lab in both runtimes, opening a separate tab with noopener/noreferrer. Runtime identity actions remain supplied by composition.

## Workspace scroll ownership

Production Online Workspace and Static Demo Workspace share a Shell bounded
by the browser's visible viewport. The sidebar and right-side Header remain visible
while the right-side Content, the sole vertical scroller for main page content,
scrolls. Normal long Workspace content must not increase the Document's height into
a page-level vertical scroller. The sidebar Brand remains at its top; navigation
that exceeds the remaining height scrolls independently.

Application Shell owns these layout constraints for every business page. Features
must not implement global navigation fixation. This requirement specifies visible
behavior, not a particular positioning or CSS technique.

Preserve navigation collapse/expansion, responsive breakpoints, selected and open
menu state, Production routes and Static hash routes, report section links and
`scrollIntoView`, feature-local horizontal scrolling and Plotly Zoom/Pan. Shell
layout must not change Backtesting Activity lifetime or authentication composition;
login, logout and authentication pages retain their normal layout outside Workspace.

## Calendar Spread composition

Calendar Spread has independent Daily and Historical Relative Value controllers under
Production's authentication gate. Since WP7, shared navigation/overviews also expose
the two admitted Static pages through formal Presentation, without online controllers.
Both runtimes compose fixed Workspace routes and a Strategy route family derived
from the same Graph. Composition supplies the runtime Strategy catalog to the shared
Shell and route adapters. Demo's nine Bundles remain independently owned by
[Demo authority](demo/ARCHITECTURE.md).
