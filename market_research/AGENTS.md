# market_research Agent Rules

继承根 [AGENTS.md](../AGENTS.md)。先读 [repository architecture](../ARCHITECTURE.md)
与 [module architecture](ARCHITECTURE.md)，再按任务进入最窄 authority：

| Task | Next authority |
| --- | --- |
| Module ownership, concepts, dependency direction | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Facts, public upstream selection, completeness, provenance or failure | [UPSTREAM.md](UPSTREAM.md) → actual Dataset / Product public contract |
| Descriptive flow and evidence interpretation | [descriptive/ARCHITECTURE.md](descriptive/ARCHITECTURE.md) |
| Fixed observation request, population, market derivation or provenance | [descriptive/OBSERVATION.md](descriptive/OBSERVATION.md) |
| Research-owned sample conversion or Analyze result association | [descriptive/ANALYZE_INTEGRATION.md](descriptive/ANALYZE_INTEGRATION.md) |
| ResearchPlan, Job / Batch control, statuses or result accounting | [descriptive/EXECUTION.md](descriptive/EXECUTION.md) |
| Numerical inputs, methods, results or statistical failures | [Analyze entry](../market_analyze/ARCHITECTURE.md) → [public contract](../market_analyze/CONTRACT.md) |

语义变更先更新 narrowest canonical authority，再修改实现；下层只能 specialize 上层 invariant。
缺失的研究方法决定必须显式记录并解决，不从旧实现、统计惯例或用户沉默推断。
Authority readiness 不等于 runtime readiness；当前无 Research execution / CLI / API。
不恢复旧 framework、compatibility、mandatory persistence 或 generic engine。
Descriptive / Conditional 不相互 import，不通过共享基类或执行引擎耦合；不创建 Conditional 空框架。
Research 仅消费 Analyze public contract；不在 Research 重定义其类型或通用统计公式。
Converter 与业务结果关联属于 Research，Analyze 不获取市场数据或依赖 Research / DataLake / Snapshot。
未来实现按真实 case colocate，仅在实际复用需求成立时提取共享能力。
所有 Python tooling 从 repository root 使用唯一根环境。

修改后执行 `poetry run pytest market_research/tests`、
`poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py`、
`poetry run ruff check market_research`、`poetry run mypy market_research/tests` 与
`git diff --check`，检查 links / anchors、根入口可达性与完整 diff。
实现变更补充受影响行为验证；跨模块改动同时执行对应 owner 的相关检查。
