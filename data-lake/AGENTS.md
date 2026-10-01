# data-lake Agent Rules

## 适用范围与 Authority 路径

本文件适用于 `data-lake/` 整棵目录，继承根 [../AGENTS.md](../AGENTS.md) 的执行政策与 [repository architecture](../ARCHITECTURE.md) 的上层边界。

1. 读取 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 DataSet / SQLite ownership、公共 persistence model、public Application Service 与 operation boundary。
2. 通过 [DATASETS.md](DATASETS.md) 选择 owning DataSet。
3. 读取该 DataSet 的 `ARCHITECTURE.md`，确认 Source、Scope、Window、identity、Record fields、completeness 与 request/result/view contract；不默认加载 sibling DataSet 或其他模块的 specialized authority。涉及 CLI delivery 时再进入 [lab authority](../lab/ARCHITECTURE.md)。

## 执行规则

- 通用 ownership 与 persistence invariant 由模块 architecture 拥有；Dataset-specific semantics 由 Dataset authority 拥有；catalog 只提供导航。
- 语义变更先更新 narrowest canonical authority；下层只能 specialize 或 constrain 上层 invariant，发现冲突须显式 reconciliation。
- 每个 DataSet exactly owns 一个 SQLite。不得引入 global database、global instrument master、跨 DataSet foreign key 或未经 authority 声明的模块依赖。
- Implementation 必须对齐 public Application Service、owning Dataset contract 与 repository runtime invariant；consumer 不直接进入 Repository、SQLite 或 Source adapter，不发布 arbitrary record-level mutation。
- `coverage` / `export` 必须真正 read-only，不 materialize missing FetchUnits、不隐式 ensure、不访问 Source；只有 `ensure` 可以创建或更新 persistence state。
- Python tooling 与 dependency workflow 必须从 repository root 使用唯一根环境；canonical namespace 为 `data_lake`，进入本目录不创建独立 Python project 或虚拟环境。
- 复用当前 credential convention，不新增 token/SQLite path semantic arguments；runtime configuration 不授予 import Snapshot 私有实现的权限。

## 验证

### Authority-only 变更

核对受影响语义、下层 specialization、所有新增相对链接及根入口可达性，并审阅包含新增文件的完整 diff。不得为文档变更提前创建 runtime 或测试框架。

在 repository root 运行现有 authority 检查与 whitespace 检查：

```bash
poetry run pytest market-snapshot/tests/test_authority_topology.py
git diff --check
```

现有 topology 检查不自动登记新的 DataSet entry，因此还须显式确认从根 architecture 经模块 architecture 和 catalog 能到达该 DataSet authority。

### Implementation 变更

Implementation 应随具体设计更新本政策中的验证命令，从 repository root 按受影响模块范围验证。检查 public request/result/view、coverage 互斥计数、ensure 逐 unit completeness 与原子写入，以及 coverage/export 无 Source I/O、无 SQLite mutation。CLI integration 同时验证 owning Dataset contract 与 lab delivery/exit-code behavior；不以共享 runtime 替代 boundary 检查。提交前审阅完整 diff，跨模块 contract 变更同时执行 producer 与 consumer 的相关检查。
