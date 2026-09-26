# web-ui generated contract feedback-loop authority

本文档从属于 [web-ui architecture](ARCHITECTURE.md)，拥有 frontend-consumed HTTP products 的 generated contract ownership、generation obligation 与 freshness feedback loop。Backend product authority 定义语义，backend HTTP contract 定义 wire contract；本文件不创建竞争性的 schema。

## 1. Feedback-loop Invariant

每个 frontend-consumed HTTP product 必须遵循同一依赖方向：

```text
backend HTTP contract
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

## 2. Per-product Ownership

每个 consuming feature 分别拥有与自身实现 co-located 的 committed OpenAPI representation 与 generated TypeScript contract：

| Frontend feature | Backend HTTP contract | Generated contract owner |
| --- | --- | --- |
| MO Option Chain | `GET /mo-option-chain` | `mo_option_chain` frontend bounded context |
| MO Premium Plane | `GET /mo-option-premium-plane` | `mo_option_premium` frontend bounded context |

两个 generated contract boundaries 平级且独立。Backend runtime 可以组合多个 product routes，但 runtime composition 不得把 sibling frontend features 强制耦合进共享业务 schema、共享 DTO ownership 或共享 feature-local contract boundary。

## 3. Generation and Freshness Obligations

出现以下任一情况时，owning feature 必须生成或更新自己的 committed OpenAPI representation 与 generated TypeScript contract：

```text
generated artifact missing
OR generated artifact stale relative to the backend HTTP contract
OR backend HTTP DTO / OpenAPI changed
```

首次实现 frontend consumer 时，即使 backend HTTP contract 本身没有在同一变更中修改，missing artifacts 仍必须生成并进入 freshness feedback loop。Authority-only 或其他不影响 contract 的变更不得无故重写 generated artifacts。

## 4. Repository-level Verification

Repository-level frontend `contract:check` 必须覆盖所有 frontend-consumed HTTP products。对每个 product，它至少确认：

1. committed OpenAPI representation 存在且与 owning backend HTTP contract 当前发布的 OpenAPI 一致；
2. generated TypeScript contract 存在且可由 committed OpenAPI representation 确定性重现。

任一 product 缺失、stale 或 generation drift 都必须使整体 check 失败。一个 product 通过不能替代或掩盖 sibling product 的失败。

## 5. Tooling Boundary

本 authority 不规定 exporter 的 Python 文件结构、npm script 的具体拼装、是否复用 helper，或 generic contract tooling abstraction。实现只需保持 per-product ownership、上述生成条件、确定性 dependency direction 与 repository-level complete coverage。
