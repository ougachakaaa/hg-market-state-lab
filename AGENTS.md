# AGENTS.md

## 适用范围与继承

本文件定义 `hg-market-state-lab` 的 repository-wide agent execution policy。进入子目录后，必须继续读取路径上最近的 `AGENTS.md`；local rule 在明确专门化本文件时优先。本继承规则只适用于执行政策，不允许下层 semantic authority 覆盖上层 invariant。

项目工作目录、启动方式与环境要求见 [README.md](README.md) 和 [DEVELOPMENT.md](DEVELOPMENT.md)。

## Progressive Disclosure

1. 先读根 [ARCHITECTURE.md](ARCHITECTURE.md)，只确定 owning module 和顶层边界。
2. 进入 owning module，读取其 local `AGENTS.md` 与 `ARCHITECTURE.md`：当前入口为 [market-snapshot/AGENTS.md](market-snapshot/AGENTS.md) 与 [web-ui/AGENTS.md](web-ui/AGENTS.md)。空的 `market-modeling/` 尚无 local policy 或 module authority。
3. 按 local catalog 或 architecture 进入相关 bounded-context entry。
4. 只读取当前任务需要的 specialized authority；不默认加载 sibling product 或其他模块文档。

`_temp_docs/` 不属于 repository authority，不参与上述导航链。除非任务明确指定其中某个文件，否则不得读取、引用或把其内容当作项目事实；需要固化的内容必须先与当前 authority reconciliation，再写入正式 authority。

## Repository-wide Rules

- 不得提交真实 API Token、密码或其他敏感信息。
- 涉及数据含义、输出结构、职责边界或 workflow 语义的变更，先更新 narrowest canonical authority，再修改实现。
- 实现必须遵循当前 authority；发现代码、同级文档或上下层 authority 不一致时，显式 reconciliation，不得静默选择或创建另一套语义。
- 下层 semantic authority 只能在上层边界内 specialize 或 constrain，不能静默推翻上层 invariant。
- 优先采用满足当前 authority 与任务要求的最小实现，不为假设需求引入框架、抽象或业务概念。
- 修改后按受影响模块的 local `AGENTS.md` 验证；跨模块 contract 变更同时执行 producer 与 consumer 的相关检查，并在提交前审阅完整 diff。
