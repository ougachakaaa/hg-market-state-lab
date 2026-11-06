# Authentication MVP V1 authority

本文件从属于 [HTTP module authority](ARCHITECTURE.md)，唯一拥有 Repository HTTP access 的用户、审批、认证持久化、JWT Cookie、限流、同源检查及 Auth HTTP contract。CLI command/delivery 归 [lab authority](../ui_cli/ARCHITECTURE.md)，Web application gate 归 [application authority](../ui_web/application.md)，市场产品仍由 [HTTP catalog](HTTP_PRODUCTS.md) 导航。

## 1. Scope and delivery status

G0 仅编码已确认的 MVP 语义、必要的输入规则与验收契约。本文件描述 G1–G4 的目标行为；G0 不代表运行中的 server 已受保护。G0 不修改生产代码、依赖、数据库、HTTP routes、页面或 generated artifacts。后续 Goal 不得把尚未实现的安全契约报告为已生效。

G1 已实现 Auth-owned SQLite、注册与审批 Public Python Service、canonical `lab auth` 以及无 HTTP app 构造的 Auth import。G2 已实现 Auth HTTP endpoints、HS256 Cookie/sliding session、统一 Access Gate、同源验证与内存限流，以及 OpenAPI/doctor 和两个 MO consumer 的 reconciliation。G3 已实现 Web 登录/注册、application gate、Cookie 身份恢复、退出、401 与旧请求隔离，以及独立 Auth generated contract 和同源 dev proxy。G4 已完成本地跨层验收；运行方式与公网开放前的部署事项见 [development guide](../DEVELOPMENT.md)。

Auth 是 `ui_http` 内的技术访问能力，不是新的 business module、HTTP runtime、Python project 或通用用户平台。所有本地和服务器访问都需要登录；不提供 local bypass。Operator 是拥有服务器操作权限的人，无 Web 管理员角色、Admin HTTP API 或管理页面。MVP 不包含 OAuth、RBAC、邮件、密码找回、验证码、Refresh Token、Redis 或复杂风控。

## 2. User identity and persistence

### Identity and credentials

- 用户使用 `username + password` 注册和登录。Username 输入必须是字符串，原始长度最多 64 个字符；只去除两端 ASCII space (`U+0020`)，再将 ASCII A–Z 转为小写。规范化结果必须匹配 `[a-z0-9][a-z0-9_.-]{2,63}`，即 3–64 个 ASCII 字符。不做 Unicode folding、全角替换或 locale-dependent normalization。HTTP 与 Python service 使用同一规则。
- 规范化 username 是唯一身份键及展示名称；`Alice` 与 ` alice ` 指向同一账号。数据库对规范化键实施唯一约束，不能只靠先查后写；并发重复注册也只有一条记录。
- Password 必须为 12–128 个 Unicode 字符，UTF-8 最多 512 bytes；拒绝无效 Unicode，不 trim、截断、大小写转换或 normalization，不要求特定字符类别。长度检查先于哈希。该规则是 MVP 的稳定输入边界。
- 存储 Argon2id 带参数与随机 salt 的编码 hash；最低配置为 memory 19456 KiB、iterations 2、parallelism 1，salt 至少 16 随机 bytes。库选择和更高成本调优属于实现，不得降低该底线。该底线依据 [OWASP password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。
- User ID 是服务端生成的稳定 UUID 字符串，独立于 username；创建时间为 UTC。持久记录的最小内容为 ID、规范化 username、password hash、status、created_at。公开身份不含 hash、password、JWT 或任何角色。

### Storage ownership

`ui_http` Auth 独占一个 SQLite 数据库，默认仓库根相对路径 `ui_http/data/auth.sqlite3`，与所有 Dataset / Snapshot / Research 存储分离。CLI 与 server 从同一 Auth composition 解析路径，不能因当前目录不同而操作另一库。可由服务器环境变量 `LAB_AUTH_DB_PATH` 指定绝对路径；普通 HTTP request 与 CLI arguments 不接受数据库路径。

G1 首次使用可创建空库及 schema；不读取、迁移、兼容或改写其他模块 SQLite。新库之外的未知或损坏 schema 必须报告 operational failure，不静默删除、重建或降级。数据库、WAL/journal 及真实凭据不得进入 Git；G1 必须先补充整个 `ui_http/data/` 的忽略规则。根 [runtime state policy](../ARCHITECTURE.md#naming-and-transition-authority) 同样适用：不新增历史状态迁移、账号保留或备份系统；空库需要重新注册审批。

完整 SQLite `quick_check` 在每个 store 首次事务及写事务执行；后续认证读取仅校验 schema/version 和读取记录，不做全库扫描。所有 SQLite 错误与损坏记录均 fail closed；不缓存 active 用户状态。

### Registration and state transitions

新用户默认为 `pending`。重复注册对四种已有状态都返回同样的通用受理结果，不替换密码、不改变状态、不重置 ID / created_at；未知用户与已有用户的响应状态、body 和 Cookie 行为一致。处理路径不得以明确可区分的快速失败暴露存在性；重复注册执行等价的有界 hash 工作，不能用固定 sleep 代替。数据库故障不能伪装为成功受理。

| Operation | Allowed transition | Repeated target state | Other existing states |
| --- | --- | --- | --- |
| approve | pending → active | active → active，无修改 | 拒绝 |
| reject | pending → rejected | rejected → rejected，无修改 | 拒绝 |
| disable | active → disabled | disabled → disabled，无修改 | 拒绝 |

状态检查与更新在同一事务内完成，CLI / HTTP 并发不产生 lost update。未知 ID 是 not found；错误状态是 invalid transition。Rejected / disabled 不可登录，不通过重新注册重新申请；MVP 无删除、改名、改密码、恢复或批量管理操作。只有 `active` 可以登录和通过每次请求的认证。

### Public Python service and CLI dependency

G1 发布 `ui_http.auth` 下的公开 Python service boundary；`create_service()` 解析 Auth-owned storage，service 提供 `register(username, password)`、`list_pending()`、`approve(user_id)`、`reject(user_id)`、`disable(user_id)`。G2 在该边界内提供 credentials verification 和按 ID 查询当前 active identity；HTTP/CLI 都不直接读写 repository/SQL。

Register 返回不揭示是否新建的受理结果。List 返回按 `(created_at, id)` 升序排列的 pending views，含 `id, username, status, created_at`；状态操作返回 `id, username, status`。公开 failure categories 为 invalid input、not found、invalid transition、authentication failed、operational failure；Python service 不返回 HTTP status，也不因 CLI caller 绕过状态规则。

公开 Python exports 为 `create_service() -> AuthService`、`RegistrationAccepted`（仅通用 `message`）、`UserIdentity`、`PendingUser`（含 timezone-aware UTC `datetime`）、`UserStatus` 及 `AuthServiceError` / `AuthFailureKind`。List 返回不可变 `tuple[PendingUser, ...]`；状态操作返回 `UserIdentity`。Failure 通过 `AuthServiceError.kind` 分类为 `invalid_input`、`not_found`、`invalid_transition`、`authentication_failed`、`operational_failure`，异常文本不含原始输入、SQL 或配置。G2 在此 boundary 发布 `verify_credentials(username, password)` 与 `get_active_user(user_id)`，只返回 active `UserIdentity`；未知、非 active 和错误密码统一为 `authentication_failed`，合法性错误仍为 `invalid_input`，数据库或存储 hash 损坏为 `operational_failure`。

Service import 和 Operator 操作不能启动/构造 HTTP app、读取 JWT secret、访问市场数据或依赖 FastAPI request context。G1 已解除 G0 discovery 记录的 `ui_http/__init__.py` eager app import side effect；现有 HTTP public entry 保持兼容，不引入第二个 launcher。CLI 仅允许导入这个公开 Auth boundary，不可进入 Auth persistence internals。

## 3. Authentication and token lifecycle

### JWT and current-user check

登录验证 password 后仅为 active 用户签发 JWT Access Token，使用固定 HS256 和服务端高熵签名密钥；拒绝 `none`、其他算法及由 token header 决定算法/密钥的行为。Required claims 为 `sub` (user ID)、`iat`、`exp` (UTC integer NumericDate)、`iss = hg-market-state-lab`、`aud = hg-market-state-lab:http`；`exp = iat + 3600`。不在 token 中保存密码、hash 或作为权限依据的 status。验证签名、algorithm、所有 required claims、issuer/audience、时间类型和 `iat <= now < exp`；不允许过期宽限。规范依据 [JWT claims](https://www.rfc-editor.org/rfc/rfc7519.html) 与 [JWT security practices](https://www.rfc-editor.org/rfc/rfc8725.html)。

每次认证都读取数据库的当前用户状态；用户不存在或不再 active 时不授予访问，即使 JWT 尚未过期。不能缓存 active 状态替代该检查。存储故障 fail closed，以安全的 500 operational error 响应；不能把故障伪装为匿名成功。禁用会阻止后续认证，不取消已经通过认证、正在执行的同步业务请求。

通过 FastAPI `Security` 和 cookie security dependency 建立认证，例如 `APIKeyCookie(auto_error=False)`，再用本契约统一处理缺失 Cookie / 无效 token，不能依赖框架默认 status/body。使用 FastAPI [Security tools](https://fastapi.tiangolo.com/reference/security/) 发布 OpenAPI `apiKey`、`in: cookie` security scheme；不新增 OAuth2/password-form 或 Authorization Bearer 备用入口。

### Cookie and sliding expiration

唯一登录 Cookie 名为 `lab_access_token`，`HttpOnly`、`Path=/`、无 Domain（host-only）、`SameSite=Strict`、`Max-Age=3600`，Expires 与 token 的 exp 一致；生产必须 `Secure`。JWT 仅通过 Cookie 交付，不在 JSON、URL、frontend storage 或日志中返回。Auth responses 使用 `Cache-Control: no-store`；所有通过认证的响应同样禁止共享/浏览器缓存，避免缓存身份响应或 Set-Cookie。

当前 frontend/API 采用 same-origin 交互，不需要 cross-site authenticated requests；部分既有 GET 会访问 Source 或写缓存，因此采用 Strict。已知约束：从外部站点导航进入时，首个跨站请求不携带该 Cookie，可能呈现未认证结果；MVP 不增加绕过或补救流程。Strict 不替代下文独立的 Origin/Referer 同源验证；G2 已实现 Cookie 与服务端同源检查，不引入 CSRF framework。

每次成功的已认证 HTTP 请求在生成最终响应时，以当时 UTC 时间重新签发 3600 秒 JWT 并更新 Cookie。这里的成功为最终 HTTP 2xx；Research 在 200 中表达 failed/partial evidence 仍属于 HTTP 成功。请求入站时必须已持有效 JWT；不能用滑动续期挽救入站时已过期的请求。

认证失败、同源失败、400/403/404/409/429、业务或 runtime 5xx、未认证公共请求均不续期。Renewal 不能只检查“存在 Cookie”，也不能在 dependency 验证通过时提前写 Cookie；只有最终成功响应可以提交续期。不得修改业务 DTO 或 error body。无 Refresh Token、token DB/session cache、撤销表、轮询或后台续期请求；持续有正常成功请求就持续滑动，无额外 absolute session lifetime。

Public Auth operations 的 Cookie 行为独立且优先：register 永远不签发或续期；login 成功只签发一次；logout 永远清除 Cookie，即使附带有效 JWT 也不触发续期。清除使用相同 name/path/domain/security attributes、`Max-Age=0` 及过去的 Expires。

Logout 不撤销已经复制的 JWT；若用户仍 active，泄露的 JWT 在过期前仍可被使用，甚至在持续成功请求下继续滑动。禁用账号可阻止后续认证，签名密钥轮换会使全部旧 token 无效；MVP 没有按 token 即时撤销。并发响应可能乱序覆盖 Cookie；尤其 logout 与已在执行的成功请求竞争时可能重新写入 Cookie。前端必须中止/隔离本客户端旧请求并阻止其恢复登录 UI，但浏览器已在途的 Set-Cookie 无法靠无状态 server 完全消除；不承诺全设备即时退出或并发严格撤销。

### Runtime configuration

Auth 配置来自 process environment；本地开发也可写入 repository root `.env`（process environment 优先），统一经 repository-level `lab_config` 读取。它不向浏览器暴露 secret，也不得写入 module-local `.env`：

| Setting | Contract |
| --- | --- |
| `LAB_AUTH_JWT_SECRET` | 必填；base64url 编码的至少 32 random bytes，解码后作为签名密钥；不得使用内建、自动生成或示例 fallback |
| `LAB_AUTH_MODE` | `production`（默认）或显式 `loopback-http`；未知值拒绝启动 |
| `LAB_AUTH_ORIGIN` | 必填，唯一 browser-facing origin，scheme/host/effective port，无 path/query/fragment；同源验证的可信目标 |
| `LAB_AUTH_DB_PATH` | 可选，语义见 storage section |

`.env` 只提供本地文件来源，不改变上表的 required / validation 语义；缺失或非法配置仍在 serving startup fail closed。`.env` 不进入 Git，production 应显式使用 server environment 变量。

Production origin 必须 HTTPS，Cookie Secure 固定开启，不接受环境变量单独关闭。`loopback-http` 仅允许 loopback listener 和显式 loopback HTTP origin，Cookie 可 `Secure=false`；默认本地前端 origin 为配置值 `http://127.0.0.1:5173`，后端 listener 为 `127.0.0.1:8011`。不允许非 loopback bind 套用该模式。所有模式仍要求 secret、数据库状态检查及登录。配置缺失/不安全时 serving startup fail closed，不回退到 no-auth。

Secret/config 校验属于 serving startup，不属于纯 `.openapi()` schema construction 或 G1 CLI 操作；不得因为可离线生成 schema 就允许未配置的 app 被 HTTP 调用。测试可显式注入临时 DB、固定时钟、合成 key/config，不提供可从网络触发的 test bypass。

## 4. HTTP contract and access order

### Auth operations

Register / login 只接受 `application/json`（可带 charset），body 必须恰好包含字符串 `username, password`，禁止未知字段、重复 JSON keys、query parameters 和隐式类型转换。原始 body 上限 4096 bytes，读取流时也必须累计限额，不能只信 Content-Length；不支持压缩 request body。所有验证先于 password hash；不得在错误 body 回显输入、password、hash、token 或数据库路径。

Minimal user identity 的固定 JSON shape 是 `{"id":"<uuid>","username":"<canonical>","status":"active"}`。

| Method / path | operationId | Access | Success / Cookie |
| --- | --- | --- | --- |
| POST `/auth/register` | register_auth_user | public | 202 `{"message":"Registration request accepted."}`；包括重复注册；不签发 token |
| POST `/auth/login` | login_auth_user | public | 200 minimal user identity；设置 Cookie |
| GET `/auth/me` | get_auth_user | authenticated | 200 minimal user identity；正常滑动续期 |
| POST `/auth/logout` | logout_auth_user | public | 204，无 body；清除 Cookie，不验证 JWT，有/无/过期 Cookie 均可 |

Me / logout 不接受 query 或 body。所有 POST 仍须同源检查；public 只表示不要求已有 JWT。注册不返回 user ID 或 existing/status 提示；pending、rejected、disabled、未知账号及密码错误的有效登录请求全部返回相同 401 body，无 403 账号状态提示。未知账号使用 dummy Argon2id verification，已有账号的失败分支采用等价验证，避免快速存在性 oracle；不承诺网络延迟的数学恒定。

Auth/access errors 使用独立 schema，固定形状为 `{"error":{"kind":"<kind>","detail":"<safe text>","param":null}}`。`param` 始终 null；不混入任何 product 的 closed kind enum：

| Status | kind | Meaning / stable detail |
| --- | --- | --- |
| 400 | invalid_request | Auth JSON、字段、长度、media type、压缩或 body bound 错误；`Invalid authentication request.` |
| 401 | authentication_required | protected path 缺失、无效、过期 JWT，或 subject 不存在/非 active；`Authentication required.` |
| 401 | invalid_credentials | syntactically valid login 未通过 credentials / active 检查；`Invalid username or password.` |
| 403 | origin_forbidden | 同源验证失败；`Same-origin request required.` |
| 429 | rate_limited | register/login 超限；`Too many requests.`；包含整数秒 `Retry-After` |
| 500 | internal_error | Auth storage / signing 等 runtime 故障；`Authentication service unavailable.` |

不发布 Auth 422、409 duplicate username 或区分账号状态的 login 错误。失败登录不清除或续期已有 Cookie。401 不做 HTML redirect；Web 根据响应状态处理，机器 caller 仍得到 JSON。产品通过 access gate 后的原有 validation/status/envelopes 不变。

### Default protection and execution order

唯一匿名 allowlist 是精确的 method/path：`POST /auth/register`、`POST /auth/login`、`POST /auth/logout`。`GET /auth/me`、MO、Research 所有路径（包括 discovery/preview）、后续 business routes 以及实际 HTTP `/docs`、`/openapi.json`、`/redoc`、`/docs/oauth2-redirect` 都必须经过认证；不存在 public health endpoint、静态业务页面、alternate product app 或 local exemption。

所有实际 HTTP surfaces，包括保留的 product-only app factories，都必须使用相同 access policy；它们只可作为离线 schema builders 消费时不需要登录，不能成为可服务的匿名替代 app。不使用仅覆盖 APIRouter 的 dependency 假定框架 docs 已受保护。

可观察处理顺序：

1. 从可信连接解析 client IP；register/login 原子地预留 rate-limit slot，超限立即 429，不读大 body、不 hash、不写用户。
2. Protected paths 通过 FastAPI Security 验证 JWT 与当前用户状态。无效身份在业务 validation、body parsing、依赖解析、Research preflight/guard 或任何 owning-module 调用前返回 401；只允许限额判断等廉价 transport 工作先行。
3. 所有有副作用的 HTTP methods 检查同源来源（public Auth POST 也包含在内），失败 403，无副作用。
4. 执行有界 parsing / endpoint validation，然后才调用 Auth service 或 owning business boundary。
5. 依据最终响应决定 Cookie 签发、清除或续期，添加 no-store；错误由 owning error handler 投影。

Middleware 可拥有早期 transport gate、限额读取与响应 Cookie，但不能替代 FastAPI Security 的身份 contract。同一请求不应重复执行昂贵 verification；认证结果可存于 request scope。Auth errors 和 Auth RequestValidationError 由本模块 Auth handler 处理，不能落入当前 chain-default validation handler；已有 MO / Research error handlers 保留产品归属。

## 5. Rate limits, client IP and browser security

### Minimal rate limiting

Register 每个 client IP 在滚动 300 秒内最多接纳 1 次；login 为滚动 60 秒内最多 5 次，两个 bucket 独立。用单调时钟，保留 `(now-window, now]` 内已接纳请求的时间戳；窗口边界刚到即可再次接纳。成功、错误密码、未知/非 active 用户、400 malformed/oversize 与 403 来源失败都计入；429 本身不追加时间戳或延长窗口。`Retry-After` 是最早接纳 slot 距离释放时间的向上取整秒，最小 1。

Limiter 必须位于 password hashing、verification、JSON parsing、数据库操作和其他高成本工作之前；并发预留必须原子化。单个 server process 内所有 composed app instances 共享 limiter，不得每请求重建。过期 IP buckets 必须清理，内存保持有界；容量耗尽时 fail closed 返回 429，不淘汰仍有效 bucket 让 caller 绕过限制。具体容量属于实现配置。

仅支持单进程内存；重启丢失计数、多个 workers/hosts 不共享、没有 distributed protection，不能替代公网入口防护。G4 必须验证并报告这些限制。

默认只信任直接 socket peer，忽略客户端自带的 `Forwarded` / `X-Forwarded-For` 等 header。MVP launcher 不启用隐式 proxy-header trust；本地 Vite proxy 后多个 browser 可能共享同一 loopback bucket。Trusted Proxy、真实 Client IP 解析及 Nginx 入口限流明确 deferred 至后续 Deployment Gate，G2 不实现代理支持，HTTP limiter 只使用直接 socket peer。若部署需要真实 client IP，必须由该 Gate 显式确认代理地址/链、入口覆盖与 header overwrite，按可信链从右向左选择首个不可信地址；禁止 wildcard trust 和任取最左侧 header。无可确定 peer 时拒绝或使用共享保守 bucket，不使用任意 header 构造新身份。

### Same-origin policy

所有非 GET/HEAD/OPTIONS HTTP 请求在副作用前验证来源，包括 register/login/logout 和 Research POST。若有 Origin，必须是一个合法、非 `null` 的 origin，按 scheme、规范化 host、effective port 与 `LAB_AUTH_ORIGIN` 精确相等；有 Origin 时不能用 Referer 覆盖失败。无 Origin 才回退到合法 Referer 的 origin。两者皆缺失、空值、malformed、多值或跨 origin 均 403。拒绝 suffix/substring matches，不将请求 Host / forwarded headers 当作可信配置。此策略采用 [OWASP origin verification guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)。

SameSite 是额外防护，不能替代来源校验。不引入 CSRF session/token framework 或宽泛 credentialed CORS。无浏览器的 HTTP caller 在 unsafe methods 也必须提供匹配的 Origin 和 Cookie；Operator CLI 走本地 Python service，不使用浏览器 cookie。

本地 React 从 frontend origin 请求相对 `/auth/*` 和 business paths，通过同源 dev proxy 到既有 backend，保持 Origin/Referer 和 Set-Cookie；G3 增加 `/auth` proxy。Backend 验证配置的 browser-facing origin `http://127.0.0.1:5173`，而非内部 upstream `:8011`；无需 CORS、frontend token parsing 或特殊 CSRF header。`localhost` 与 `127.0.0.1` 不混用。

安全 methods 不提交用户操作或 Research execute；既有 MO GET 内部数据准备副作用仍由产品拥有，不因此重定义为写 API。通过认证的 GET 包含滑动 Cookie，不能缓存或开放跨站读取；本契约不重新分类既有产品业务流程。

## 6. OpenAPI, CLI readiness and product reconciliation

G2 在 composed runtime 和 product contract builders 中发布 Cookie security scheme、protected operation security requirement、公共操作的 `security: []`、Auth schemas 及真实 access failure responses；Auth envelope 用独立 component，与产品 error enum 分离。MO / Research request/response DTO、原 failure classification 和 Research HTTP bounds / process-wide execution guard 不变。

离线 `.openapi()` 与 contract exporter 不通过实际 HTTP、不需要真实密码/secret、不创建默认用户库；它们生成的 security contract 与 serving 相同。HTTP schema/docs tests 必须使用显式合成认证，或在仅检查 schema 时直接 `.openapi()`；不得为现有匿名 TestClient 测试保留 bypass。Descriptive Research HTTP 仍无 Web consumer，继续不生成该产品的 Research TypeScript；单独的 [Online Futures Basis Research](products/futures_basis_research/http-contract.md) 是另一个 HTTP product，由自己的 frontend feature 拥有 generated OpenAPI/TypeScript，不改变这里的 Auth 语义。

现有 `lab doctor` 用匿名 `/openapi.json` 判定 healthy，与新访问策略冲突。G2 将其 readiness 改为识别受保护 OpenAPI 的预期 401 Auth envelope，报告 `running / authentication required`（非失败）；不读取凭据、不登录、不新开 public health route。200 OpenAPI 只作为 G0/G1 旧运行状态识别；受认证的 G2 runtime 不得匿名返回 200。实际 schema 生成与 freshness 继续走离线 builder。

G2 实际改变 OpenAPI 时更新已有 MO committed OpenAPI / TypeScript；G3 添加 application-owned Auth generated boundary，按 [Web contract authority](../ui_web/contracts.md) 覆盖全部 consumers。G0 只改 authority，禁止提前生成不存在的 routes 或手写 TypeScript schema。

MO 的 auth non-goal 解释为“产品不拥有认证协议”，不再是运行时匿名承诺；Research 的 acquisition acknowledgment 继续是采集知情确认，不能替代认证。通过认证也不授予公网部署批准：Research execute 的路由暴露、可信代理、HTTPS 终止和正式入口防护仍须后续 Deployment Gate 决策。

## 7. Goals and acceptance gates

| Goal | Scope / dependencies | Required acceptance |
| --- | --- | --- |
| G1 — User Persistence & Approval CLI | 依赖本 authority；Auth-owned SQLite、Argon2id、public service、`lab auth`、storage ignore；不新增 HTTP/Web | 唯一性、状态事务与 CLI delegation 可由临时存储验证 |
| G2 — FastAPI Authentication | 依赖 G1；既有 runtime 的 Auth routes、Security/JWT/Cookie、gate、限流/同源、配置和 doctor/OpenAPI reconciliation | 默认保护、失败无副作用、续期/退出、产品契约兼容及生成检查 |
| G3 — Frontend Integration | 依赖 G2；application Login/Registration/gate、同源请求、logout、401、Auth generated boundary、dev proxy | 全局认证 lifecycle、无 Token JS/storage、两个 MO surfaces 和完整 freshness |
| G4 — E2E & Final Reconciliation | 依赖 G1–G3；browser/CLI/HTTP 整体验收与最终 reconciliation | 完整用户旅程、安全 negative cases、限制和部署 deferred evidence |

上述 Required acceptance 由下列逐 Goal 条件补全；不得把 production implementation 标为 G0 工作。

### G1 gate

- 临时 SQLite 验证新建 pending、重启可读、规范化冲突和并发重复只建一条；重复注册永不覆盖任意状态的 hash / ID / created_at。无明文密码，hash 确认为 Argon2id 且满足参数底线。
- 覆盖 username/password 边界、无效输入、事务状态矩阵、重复目标幂等、未知 ID、损坏 schema 和 operational failure；不修改默认用户数据或任何市场库。
- Canonical `lab auth pending/approve/reject/disable` 可直接委托公开 service；按 CLI contract 输出/退出码，pending 空结果成功，hash 不进入输出；CLI import/执行不构造 HTTP app、不要求 JWT secret。
- 从根运行适用的 Auth + `ui_cli/tests` 测试、Ruff/mypy 和 boundary 检查；根项目安装新增 hash dependency，不创建 module-local runtime。G1 不声称 HTTP 已受保护。

### G2 gate

- 注册 202 无 Cookie、重复不可枚举；pending/rejected/disabled/错误密码/未知用户统一登录失败；active 登录 200、me 200、logout 204。所有 failure statuses、JSON shape 和 Cookie attrs 符合本文。
- 固定时钟验证 3600 秒 exp、边界过期、缺失/错误 claims、错误签名/算法、每个成功 2xx 的滑动、业务 200 partial renewal、所有失败不续期，以及 logout 清除优先。重启不保存 JWT/session cache。
- 登录后 disable，旧 token 在下一请求失败；数据库故障 fail closed。未经认证的 malformed business POST 不解析/不执行，不调用市场 service、不取得 Research guard。
- 所有 composed/product app、docs/schema 和新 route 默认受保护；离线 schema 不要求 secret 或 DB，不存在环境/网络 bypass。缺失 key、不安全 production/local 配置和代理伪造均有 negative tests。
- 滚动窗口/并发 slot/失败请求计数/重启限制、chunked oversize/字段边界、Origin/Referer 缺失/null/伪造与正常 dev origin 都有检查；先 limiter 后 hash，先 access 再业务。
- 原 product DTO/errors/resource bounds/guard 的 tests 在认证上下文中继续通过；Auth validation 不污染 product errors。Doctor 识别 protected readiness；运行 HTTP/CLI 适用测试、Ruff/mypy、MO contract generation/freshness 和消费者检查。

### G3 gate

- 无 Cookie/过期时只显示 application 登录/注册入口；me 检查期间不发产品请求。注册成功显示统一“已受理，等待审批”提示，不当作登录；批准后可登录并访问两个独立 MO surfaces。
- 登录/me/logout 消费 generated wire types，Token 不进入 JS、storage、URL 或任何 frontend refresh loop。401 统一关闭业务 gate 并隔离旧结果；403/429/500 不误报为账号不存在/待审批，Retry-After 可展示。
- Same-origin proxy + Cookie 在真实 loopback HTTP 工作；logout 中止/隔离旧请求并回到匿名 gate，多次退出和过期退出都可用；不把 logout 网络失败误报为服务端已清 Cookie。
- Auth artifacts 由 application 拥有，MO artifacts 仍 co-located；运行 `contract:check`、frontend tests/build/lint，补正常/失败/过期/并发 stale-result 的有意义测试。保持默认 MO entry 和 sibling feature independence。

### G4 gate and deferred boundary

使用隔离数据库和合成密钥完成 browser → register → CLI pending/approve → login → 两个 MO surfaces → me/sliding → logout；另验 rejected/disabled、重复注册不改密码、超限、跨站拒绝、过期 401、所有 docs/schema 受保护、无配置拒绝 serving、离线 export 不受影响。业务 provider 可用性与身份认证分别验证，不能用 auth 成功证明真实数据已可用。

实际 HTTPS 配置下验证 Secure/SameSite/HttpOnly 和 no-store；loopback 模式验证不允许外网 bind。不需要为验收部署公网，但必须记录未完成的公网 Deployment Gate。Research 使用确定性 service fixture 验证认证先行且原 bounds/guard 保留，禁止通过验收对默认缓存执行高成本采集。

G4 运行受影响 producer/consumer 的本地规则检查和有界 E2E，审阅完整 diff，报告实际执行证据、失败和限制。唯一明确 deferred concern 是部署拓扑/可信代理/公网暴露与入口防护；无状态 logout/concurrency、单进程 limiter、无恢复/重置能力是已接受的 MVP 限制，不据此暗中加入 session store、Redis 或新管理功能。

G0 discovery 未发现 G1 必须等待的新业务 Decision Gap；本文的规范化、输入界限、状态矩阵、service boundary 与 CLI delivery 已确定。后续发现与上层 invariant 冲突时必须先 reconciliation；Deployment Gate 的未决项不阻塞本地 G1–G4 实现，也不代表已获公网开放许可。
