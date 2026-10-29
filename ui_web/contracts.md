# ui_web generated contract feedback-loop authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，拥有 frontend-consumed HTTP products 的 generated contract ownership、generation obligation 与 freshness feedback loop。Owning business module authority 定义产品语义，[ui_http](../ui_http/ARCHITECTURE.md) HTTP contract 定义 wire contract；本文件不创建竞争性的 schema。

## 1. Feedback-loop Invariant

每个 frontend-consumed HTTP product 必须遵循同一依赖方向：

```text
owning module semantic authority
        ↓
ui_http HTTP contract
        ↓
ui_http published OpenAPI
        ↓
committed generated OpenAPI representation
        ↓
generated TypeScript contract
        ↓
frontend request adaptation
        ↓
contract freshness check
```

OpenAPI 与 TypeScript artifacts 是 backend HTTP contract 的生成表示，不是独立 semantic authority。Frontend 不得手工维护与 backend 竞争的 response schema，也不得从 generated artifacts 反向定义 backend semantics。

## 2. Consumer Ownership

每个 consumer 分别拥有与自身实现 co-located 的 committed OpenAPI representation 与 generated TypeScript contract；产品归 consuming feature，Auth 归 application：

| Frontend feature | Backend HTTP contract | Generated contract owner |
| --- | --- | --- |
| MO Option Chain | [`GET /mo-option-chain`](../ui_http/products/mo_option_chain/http-contract.md) | `mo_option_chain` frontend bounded context |
| MO Premium Plane | [`GET /mo-option-premium-plane`](../ui_http/products/mo_option_premium/http-contract.md) | `mo_option_premium` frontend bounded context |
| Application Authentication (G3 target) | [Auth HTTP contract](../ui_http/AUTHENTICATION.md#4-http-contract-and-access-order) | application Auth boundary，独立于 MO features |

两个 generated contract boundaries 平级且独立。Backend runtime 可以组合多个 product routes，但 runtime composition 不得把 sibling frontend features 强制耦合进共享业务 schema、共享 DTO ownership 或共享 feature-local contract boundary。

Application Auth 不是市场 feature；其 committed OpenAPI / TypeScript 与 application Auth consumer 共址（例如 `src/app/auth/api/`），不进入 MO feature 或 shared DTO。G2 实际改变 security scheme / access responses 时，更新已有产品 artifacts；G3 首次实现 Auth consumer 时生成其独立 artifacts 并纳入同一 generation/freshness loop。所有 consumer 的发布表示必须忠实反映运行时 access requirement；产品 DTO 不因此合并。G0 无实际 OpenAPI 变更，不生成这些 artifacts。

## 3. Generation and Freshness Obligations

出现以下任一情况时，owning feature 必须生成或更新自己的 committed OpenAPI representation 与 generated TypeScript contract：

```text
generated artifact missing
OR generated artifact stale relative to the backend HTTP contract
OR backend HTTP DTO / OpenAPI changed
```

首次实现 frontend consumer 时，即使 backend HTTP contract 本身没有在同一变更中修改，missing artifacts 仍必须生成并进入 freshness feedback loop。Authority-only 或其他不影响 contract 的变更不得无故重写 generated artifacts。

## 4. Repository-level Verification

Repository-level frontend `contract:check` 必须覆盖所有 frontend-consumed HTTP products 及已实现的 application Auth contract。对每个 consumer，它至少确认：

1. committed OpenAPI representation 存在且与 owning backend HTTP contract 当前发布的 OpenAPI 一致；
2. generated TypeScript contract 存在且可由 committed OpenAPI representation 确定性重现。

任一 product 缺失、stale 或 generation drift 都必须使整体 check 失败。一个 product 通过不能替代或掩盖 sibling product 的失败。

Contract export 使用离线 `.openapi()`，不通过受保护的 HTTP schema endpoint、不需要真实 secret/用户库，也不创建生产状态。Offline builder 不能发布一份删除 security metadata 的竞争性 contract；可被 HTTP 服务的任何 app 都遵循 Auth gate。Research 仍无 Web consumer，不因增加认证自动新增 Research generated types。

## 5. Tooling Boundary

本 authority 不规定 exporter 的 Python 文件结构、npm script 的具体拼装、是否复用 helper，或 generic contract tooling abstraction。实现只需保持 per-product ownership、上述生成条件、确定性 dependency direction 与 repository-level complete coverage。
