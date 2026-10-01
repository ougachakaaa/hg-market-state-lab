# data-lake Agent Rules

## 适用范围与 Authority 路径

本文件适用于 `data-lake/` 整棵目录，继承根 [../AGENTS.md](../AGENTS.md) 的执行政策与 [repository architecture](../ARCHITECTURE.md) 的上层边界。

1. 先读取 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 DataSet / SQLite ownership、public boundary、依赖方向与下一份 authority 的选择。
2. 按任务选择公共专题：domain / persistence / Scope / Window / FetchUnit / Record / mutation flow 读取 [DOMAIN_MODEL.md](DOMAIN_MODEL.md)；Application Service / coverage / ensure / export / public result / runtime 调用约束读取 [APPLICATION.md](APPLICATION.md)。进入 DataLake 不意味着默认读取全部 specialized authority。
3. 涉及具体 Dataset 时，通过 [DATASETS.md](DATASETS.md) 进入 owning Dataset 的 `ARCHITECTURE.md`，读取 domain specialization；consumer contract / public service implementation 再进入其 `SERVICE.md`。Domain 任务不默认读取 service / CLI，具体 implementation 读取与任务有关的公共 authority 和 Dataset authority，不默认加载 sibling Dataset。
4. 涉及 CLI delivery 时再读取 [lab authority](../lab/ARCHITECTURE.md)，不默认加载其他模块的 specialized authority。

## 执行规则

- 模块 architecture 拥有稳定 ownership 与模块边界；公共领域与 persistence invariant 由 DOMAIN_MODEL.md 拥有；公共 Application contract、failure taxonomy 与 export snapshot invariant 由 APPLICATION.md 拥有；Dataset ARCHITECTURE.md 拥有 domain specialization，SERVICE.md 拥有 consumer contract；CLI parsing / serialization / delivery / exit-code mapping 由 lab 拥有，Dataset authority 不定义 CLI option names；catalog 只提供导航。
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

现有 topology 检查不自动登记新的 DataSet entry，因此还须显式确认从根 architecture 经模块入口可到达两个公共专题，并经 catalog、Dataset ARCHITECTURE.md 可到达 SERVICE.md；同时核对 section anchors、semantic owner 唯一性、transport-neutral boundary、semantic/wire types、failure 分类及 export snapshot invariant。已有实现与新目标不一致时显式记录待实现 reconciliation，不虚称实现完成。

### Implementation 变更

Implementation 应随具体设计更新本政策中的验证命令，从 repository root 按受影响模块范围验证。检查 public request/result/view、coverage 互斥计数、ensure 逐 unit completeness 与原子写入，以及 coverage/export 无 Source I/O、无 SQLite mutation。CLI integration 同时验证 owning Dataset contract 与 lab delivery/exit-code behavior；不以共享 runtime 替代 boundary 检查。提交前审阅完整 diff，跨模块 contract 变更同时执行 producer 与 consumer 的相关检查。

DataLake core implementation 的正式测试位于 `data-lake/tests/`。从 repository root 使用根 Poetry environment 执行：

```bash
poetry run pytest data-lake/tests
poetry run pytest lab/tests
poetry run ruff check data-lake lab
poetry run mypy data-lake lab
poetry run pytest backend-api/tests/test_architecture.py market-snapshot/tests/test_authority_topology.py
git diff --check
```

根 package registration 或 Python tooling configuration 改变时，从根目录执行 `poetry install`，再确认 `poetry run python -c "import data_lake"` 和 `poetry run pytest`。Core tests 使用 test-local fake Dataset / Source 与临时 SQLite，不需要真实 provider credential，也不调用外部 Source。Public facade tests 直接验证 attributes；internal Repository、Source collaborator 与 SQLite 不作为 consumer boundary。

Calendar tests 使用 fake trade_cal client 与临时 owned SQLite；验证逐日 completeness、semantic identity、credential lazy resolution、export snapshot、public failure taxonomy 及 lab JSON / exit codes，不依赖真实 token。
