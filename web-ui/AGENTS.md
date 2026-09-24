# web-ui Agent Rules

## 适用范围

本文件适用于 `web-ui/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 presentation ownership 与 backend contract 依赖方向。
2. 从 [frontend feature catalog](FEATURES.md) 选择任务所属的 vertical slice，再进入其 co-located feature authority。
3. 只有 Guide 明确依赖某项 backend semantics 或 HTTP transport 时，才读取对应 product entry、read/backend authority 或 HTTP contract。

普通 frontend 任务不读取 Source Capture、Raw Artifact、Analysis Preparation internals、CSI1000 5D 或其他无关产品 authority。

## 执行规则

- `web-ui/` 是独立 npm project；依赖、测试、构建和 lint 均在本目录执行。
- frontend 只拥有 request adaptation、presentation state、visual encoding、interaction 与用户可见的 empty/error presentation。
- 不在 frontend 重新推导 product identity、contract universe、price fallback、completeness、financial formula 或 backend null/zero semantics。
- Markdown authority 定义语义，backend OpenAPI 是 wire contract 的机器可读表达；不得手工维护竞争性的 response schema。
- backend HTTP DTO/OpenAPI 改动后运行 `npm run contract:generate` 并提交生成的 JSON 与 TypeScript；其他变更不得无故重写生成 contract。

## 验证

在 `web-ui/` 中按影响范围运行，提交前完整验证默认为：

```bash
npm run contract:check
npm run test
npm run build
npm run lint
```
