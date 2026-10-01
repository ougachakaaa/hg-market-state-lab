# data-lake Agent Rules

## 适用范围与 Authority 路径

本文件适用于 `data-lake/` 整棵目录，继承根 [../AGENTS.md](../AGENTS.md) 的执行政策与 [repository architecture](../ARCHITECTURE.md) 的上层边界。

1. 读取 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 DataSet / SQLite ownership、公共 persistence model 与 operation boundary。
2. 通过 [DATASETS.md](DATASETS.md) 选择 owning DataSet。
3. 读取该 DataSet 的 `ARCHITECTURE.md`，确认 Source、Scope、Window、identity、Record fields 与 completeness；不默认加载 sibling DataSet 或其他模块的 specialized authority。

## 执行规则

- 通用 ownership 与 persistence invariant 由模块 architecture 拥有；Dataset-specific semantics 由 Dataset authority 拥有；catalog 只提供导航。
- 语义变更先更新 narrowest canonical authority；下层只能 specialize 或 constrain 上层 invariant，发现冲突须显式 reconciliation。
- 每个 DataSet exactly owns 一个 SQLite。不得引入 global database、global instrument master、跨 DataSet foreign key 或未经 authority 声明的模块依赖。
- 当前阶段只进行 Semantic Decision Encoding / Authority reconciliation，不新增 Python、SQL DDL、migration、Source client、CLI 或 runtime integration。
- 未来 Python tooling 与 dependency workflow 必须从 repository root 使用唯一根环境；进入本目录不创建独立 Python project 或虚拟环境。

## 验证

当前 authority-only 变更须核对受影响语义、下层 specialization、所有新增相对链接及根入口可达性，并审阅包含新增文件的完整 diff。不得为文档变更提前创建 runtime 或测试框架。

在 repository root 运行现有 authority 检查与 whitespace 检查：

```bash
poetry run pytest market-snapshot/tests/test_authority_topology.py
git diff --check
```

现有 topology 检查不自动登记新的 DataSet entry，因此还须显式确认从根 architecture 经模块 architecture 和 catalog 能到达该 DataSet authority。未来 implementation 的验证要求应随其设计更新本政策。
