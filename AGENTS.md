# AGENTS.md

## Naming transition routing

The [repository mapping](ARCHITECTURE.md#naming-and-transition-authority) defines canonical filesystem and namespaces; all entry paths and local policies below use those identities. Completed migration scope and verification remain in Git history.

## 适用范围与继承

本文件定义 `hg-market-state-lab` 的 repository-wide agent execution policy。进入子目录后，必须继续读取路径上最近的 `AGENTS.md`；local rule 在明确专门化本文件时优先。本继承规则只适用于执行政策，不允许下层 semantic authority 覆盖上层 invariant。

Repository-level Python runtime invariant 见 [ARCHITECTURE.md](ARCHITECTURE.md)，工作目录、启动方式与环境要求见 [README.md](README.md) 和 [DEVELOPMENT.md](DEVELOPMENT.md)。

## Progressive Disclosure

1. 先读根 [ARCHITECTURE.md](ARCHITECTURE.md)，只确定 owning module、顶层边界与 repository-level Python runtime/CLI ownership；CLI 使用与示例进入 [lab usage guide](ui_cli/README.md)（usage-only，不是 authority），CLI semantics 与 delegation 进入 [lab authority](ui_cli/ARCHITECTURE.md)，当前根开发环境与 runtime 状态再读 [DEVELOPMENT.md](DEVELOPMENT.md)。
2. 进入 owning module，读取其 local `AGENTS.md` 与 `ARCHITECTURE.md`：当前入口为 [data_lake/AGENTS.md](data_lake/AGENTS.md)、[data_snapshot/AGENTS.md](data_snapshot/AGENTS.md)、[market_research/AGENTS.md](market_research/AGENTS.md)、[market_backtesting/AGENTS.md](market_backtesting/AGENTS.md)、[market_statistics/AGENTS.md](market_statistics/AGENTS.md)、[ui_http/AGENTS.md](ui_http/AGENTS.md) 与 [ui_web/AGENTS.md](ui_web/AGENTS.md)。`market_statistics` 已有独立 Python numerical runtime；`market_backtesting` 拥有 Position-Driven Core V1 与 W2 Policy；当前交付状态、剩余工作及实现差异从其 module authority 进入；`market_modeling` 尚无 local policy 或 module authority，不得预先创建内部设计。
3. 按 local catalog 或 architecture 进入相关 bounded-context entry。
4. 只读取当前任务需要的 specialized authority；不默认加载 sibling product 或其他模块文档。

Repository-root operational Tasks / Runs / Gates and shared execution evidence enter
[workbench/AGENTS.md](workbench/AGENTS.md). Workbench is outside the business/interaction
module taxonomy; continue into business authority only when an approved Task needs it.

`_temp_docs/` 不属于 repository authority，不参与上述导航链。除非任务明确指定其中某个文件，否则不得读取、引用或把其内容当作项目事实；需要固化的内容必须先与当前 authority reconciliation，再写入正式 authority。

## Progressive Disclosure：Authority authoring

Progressive disclosure 同时约束已有 authority 的读取和新 authority 的创建、落位与扩展。执行 Semantic Decision Encoding、authority design / reconciliation、新 module / product / capability / study / dataset authority 落位或已有 authority 的较大扩展时，必须判断新语义应进入现有 authority，还是已经形成独立 concern，需要下层专题文档或 catalog；不得默认追加到最近的 `ARCHITECTURE.md`。

拆分依据是 semantic ownership 与任务读取路径，不设机械的行数或 KB threshold。当文档同时拥有可独立变化的 concern、不同任务只需要其中一部分、上层开始承载大量 schema / operation contract / workflow / formula / protocol / implementation-oriented invariant、新内容形成稳定 bounded contract、局部任务必须加载大量无关语义，或 catalog / module entry / specialized contract 层级已自然出现时，应主动考虑拆分。

上层 authority 应尽量只保留 identity / purpose、ownership、stable boundaries、critical invariants、dependency direction、navigation 与选择下一份文档所需的最小上下文。专题 schema、contract、workflow 与具体 product semantics 应归属 narrowest canonical authority；下层只能在上层 invariant 内 specialize 或 constrain。

对于用户已确认的较大设计语义，Agent 必须主动组织合理 authority topology，不等待额外的拆分请求，也不为了避免创建文件而强行合并独立 concern。只有真实、稳定、可独立消费的 authority concern 才建立新层级；不得为形式过度拆分、把每个小概念拆为文件，或为尚不存在的需求预建 framework / abstraction。目标路径为：

```text
stable top-level entry
    ↓
module / bounded-context navigation
    ↓
specialized authority / contract
    ↓
implementation details
```

较大的 authority 落位结束前，必须自检：

- 能否从稳定入口逐层发现所需语义，局部任务是否仍须加载大量无关内容。
- 同一语义是否有唯一 canonical owner，specialized details 是否泄漏到上层。
- 新文档是否拥有独立 semantic responsibility，navigation / inheritance / ownership 是否明确。

已经明显需要的拆分必须在本次 authority 落位中完成，不将“未来再整理文档”作为默认 deferred work；真正需要新 semantic decision 的 gap 应明确记录，不以文档重组发明业务语义。

## Pre-production Publication / Run retention

**用户已明确决定：本项目尚未正式投产；只有用户后续明确宣布投产，才进入 Production 数据保留阶段。** 公开 GitHub 仓库、GitHub Pages Demo、`production` 配置模式、CI 通过或阶段验收，均不构成投产宣告。Agent 不得自行推定已经投产。

- 正式投产前，仓库自身开发环境中的 **所有 Publication 与 Run 历史数据均可破坏性清理或重建**。适用范围包括 Research Publication Store（含已发布 Manifest、bundle、Layer/View 与其保留的 source evidence 副本）、Research / Backtesting Run Store，以及其他仓库自有的开发期运行记录和派生执行产物。允许按任务需要直接删除、重置或替换；旧记录**不要求迁移、保留、向后兼容或自动恢复**。不得仅为了保护这些开发期旧数据而引入 legacy storage、兼容层或迁移框架。
- 这是一项**开发期数据保留策略及针对性清理授权**，不是允许随意删除所有文件。执行破坏性操作前必须辨认具体 store root、所属环境与清理范围；不得波及源码、Authority、已提交的正式证据、原始/外部市场数据、DataLake 数据集缓存、凭证、其他用户/环境的数据或不明确归属的目录。不得在没有明确业务需求时增加启动即自动清库的行为；实施清理后在任务报告中说明实际删除范围。
- 此规则只放宽**历史开发数据的保留义务**，不放宽运行中的业务契约、发布身份/引用一致性、权限隔离、完整性验证、安全约束或 Public Demo 真实数据与授权门槛。
- 用户明确宣布投产后，本项破坏性清理授权立即失效；任何生产数据删除、清库或不兼容存储切换，均须重新制定数据保留/迁移方案并获得明确批准。

## Repository-wide Rules

- 不得提交真实 API Token、密码或其他敏感信息。
- 涉及数据含义、输出结构、职责边界或 workflow 语义的变更，先更新 narrowest canonical authority，再修改实现。
- 实现必须遵循当前 authority；发现代码、同级文档或上下层 authority 不一致时，显式 reconciliation，不得静默选择或创建另一套语义。
- 下层 semantic authority 只能在上层边界内 specialize 或 constrain，不能静默推翻上层 invariant。
- Python dependency installation、resolution 与 Poetry tooling 必须从 repository root 使用唯一环境；进入 owning module 只切换 semantic authority，不切换 Python project 或虚拟环境。
- Repository runtime configuration（`TUSHARE_*`、`LAB_AUTH_*`、`LAB_RESEARCH_PUBLICATION_ROOT` 等）只从 process environment 或 repository root `.env` 经 `lab_config` 读取；process environment 优先。不得在模块内建立 `.env`、独立 dotenv 读取或直接 `os.environ` 配置读取；tracked template 是根 `.env.example`。细节与验证见 [config Agent Rules](config/AGENTS.md)。
- 根 `.venv` 是 repository 唯一 Python environment；不得保留 module-local `.venv`。共享 dependency graph 或根 `.venv` 不构成 cross-module import permission；跨模块依赖仍必须遵守 public boundary、稳定依赖方向与 architecture tests。
- 优先采用满足当前 authority 与任务要求的最小实现，不为假设需求引入框架、抽象或业务概念。
- 修改后按受影响模块的 local `AGENTS.md` 验证；跨模块 contract 变更同时执行 producer 与 consumer 的相关检查，并在提交前审阅完整 diff。
