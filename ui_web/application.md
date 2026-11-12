# ui_web application integration authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，并遵循 [presentation architecture](presentation-architecture.md) 定义的内部 ownership boundary；它只拥有 Web application 的 entry、feature discovery/navigation、layout/shell 与 composition boundary。Ordinary UI、application-level theme 与 CSS policy 遵循 [UI system authority](ui-system.md)。正式 frontend surfaces 由 [feature catalog](FEATURES.md) 导航；各 surface 的产品与 visualization 语义仍由其 co-located feature authority 拥有。

## 1. Application Surfaces

Web application 以 Research 为登录后默认入口，包含三个一级业务区：

```text
Daily Data → MO Option Chain / MO Premium Plane（已实现）
Research → Research Catalog & Workspace / Research Explorer（已实现）；Futures Basis Online Research（已实现 Web Consumer）
Backtesting → Futures Roll Long（WP7 Web Consumer 已实现）
```

登录后默认进入 `/research`，不提供独立宣传首页。三个既有在线 feature 保持可发现、可访问且相互独立；WP3 Research Catalog 是只读发现入口。Futures Basis Online Research 已完成 WP8-B Web Consumer，并复用在线和离线共享 Reader。导航和 URL 由 [Workspace authority](workspace.md) 细化。

## 2. Application Ownership

Application shell 只拥有：

```text
application entry
feature discovery and navigation
application layout / shell
feature composition boundary
authentication state and access gate
login / registration / logout interaction
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

## 3. Feature Independence

MO Option Chain、MO Premium Plane、Research Catalog、Research Explorer、Futures Basis Research 与 Backtesting 保持独立 frontend bounded contexts。它们不共享产品 identity、backend DTO、query state、presentation state 或 visualization semantics，也不从 sibling feature 的 response 或 local state 派生自己的事实。

Application composition 不改变各 feature 的 backend dependencies，也不表示 backend products 存在业务耦合。切换 surface 时 feature state 的 React lifecycle 或持久化机制属于实现细节；无论采用何种机制，一个 feature 都不得读取、覆盖或重新解释另一个 feature 的 local state。

## 4. Implementation Boundary

本 authority 不规定 router library、精确 component/props、component tree、mounting strategy、CSS filename 或 state-management library；实现选择遵循 `ui-system.md` 和 [Workspace authority](workspace.md)，不得为未来 feature 引入 plugin 或 generic runtime。

## 5. Application Authentication (G3 implemented)

认证 HTTP、用户状态、审批、Cookie、限流与同源协议唯一归 [Authentication MVP V1](../ui_http/AUTHENTICATION.md)。本节只拥有 application 交互和 gate；G3 已实现下述交互，G4 已完成本地跨层验收。

Login / Registration 是 application-level 入口；普通登录进入 Research Workspace，直接访问已知深层页面且认证成功时保留该页面。用户可切换 Research Catalog、Research Explorer 和两个 MO feature；Futures Basis Research 已实现 Web Consumer。登录状态不属于各 feature 的 local query/presentation state，不经 sibling feature 共享；shell 不因此接管产品 query、DTO 或图表语义。

同一认证 lifecycle 内，已取消的 feature 请求若仍返回 401，也必须关闭该 gate；已关闭的旧 lifecycle 不得影响后续登录。

Application 管理以下状态及行为：

- 启动/重新载入时只执行一次按当前 application lifecycle 发起的 `/auth/me` 检查；checking 时不 mount 会发业务请求的 surface。成功则 authenticated，401 则 anonymous；网络/500 错误提供失败与重试状态，不把它当作确认退出。
- Anonymous 显示 username/password 登录和注册入口。注册 202 只显示通用“申请已受理，等待 Operator 审批后登录”，不获取用户 ID、不判断是否重复、不自动登录或轮询审批。Operator 从服务器 `lab auth` 处理；无 Web admin surface。
- 登录成功依据最小 user identity 开放 gate；失败保留通用 credentials 错误，不能根据 401 猜测账号是否存在、pending 或 rejected。400、403、429（含 Retry-After）、500 有各自可理解的反馈。
- 任一受保护业务/me 请求 401 使 application 返回匿名 gate，停止新业务请求、中止/隔离旧请求并清除本客户端已显示的身份/业务结果；stale success 不得恢复登录或旧结果。403 来源拒绝、429 或产品业务错误不自动清除登录状态。
- Logout 发同源 POST，pending 期间阻止新业务请求并中止/隔离旧请求。204 后清除本地身份与产品结果并回到匿名入口；失败时保留可重试的退出状态，不声称服务端已清 Cookie。过期或缺失 Cookie 的 logout 仍可正常完成。

Application 只消费服务端 identity；JWT 只由浏览器 HttpOnly Cookie 管理，不生成、解析、读写、刷新或保存在 local/session storage。请求使用相对同源 URL 和 Cookie credentials；不做后台续期、me heartbeat 或 retry-on-401 刷新。登录/me 的用户信息不能用前端时间或旧 local state 取代服务器认证。

Auth request adaptation、generated schema/types 及 React lifecycle 属于 application 的 Auth concern（可放在 `src/app/auth/`，incidental filenames 由实现决定），独立于产品 DTO。Domain-neutral `shared/http` 可以传递 401/credentials 信号，但不能依赖 app/feature 或解释产品 state；由 application 显式组合 callback/context。不得为了全局 gate 引入通用 feature runtime。

G3 的本地 dev proxy 增加 `/auth`，保持正常 frontend origin 和 Set-Cookie；浏览器不直接调用不同 port 的 backend。Cookie/CSRF 和 loopback/production 配置遵循 Auth authority。无 local bypass，UI gate 也不能替代后端 access check。无状态 logout 在途 Cookie 竞争的限制由 Auth authority 明示，frontend 不承诺全设备即时撤销。
