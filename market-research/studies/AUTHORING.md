# Research Study Authority Authoring

本文件是新建 retained Study 的稳定入口。Research 模块边界与现有 Study 入口见 [market-research architecture](../ARCHITECTURE.md)；runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。Study Intention 经 [Review](REVIEW.md) 的结构化与 semantic decision workflow，形成当前 Study 的 Canonical Study Authority；Agent 不得自行发明未给出的研究语义。

## Study identity 与完成范围

一个 Study 围绕一个 bounded research question / small hypothesis，拥有自己的研究语义与 retained evidence。新 Study 的 canonical authority 必须回答 [Schema](SCHEMA.md) 中 Question、Inputs、Method、Results、Limitations、Acceptance 六个 semantic areas。Study 是一个 semantic authority unit，可以由单个或多个 Markdown 文件构成；`studies/<study_package>/ARCHITECTURE.md` 始终是稳定入口。简单 Study 保持单文件；复杂 Study 按语义复杂度建立可导航的 specialized authority，不为形式统一拆分。独立的 implementation 位置是同名 `src/market_research/studies/<study_package>/`；完成 authority 不自动启动 implementation 或 Study execution。

## 创建隔离与导航

新建 Study 必须 Research-semantic self-contained：研究问题、population、predictor、target、regime、grouping、Observation、Analysis、统计解释和 evidence contract 中定义研究证据含义的语义，均由当前 Study 本地拥有，即使与既有定义相同也须在当前 Study 明确写出。创建时不得主动搜索 sibling Studies、其 retained artifacts、既有 `market-research/shared/*` 或 implementation 来继承 Research semantics / helper。Sibling Study 可作为 related work、历史 evidence 或导航被引用，但不成为 semantic owner 或 dependency。研究语义、公式、分组逻辑及 Study-local analytical code 允许有意重复；相似性不触发 shared 抽取、跨 Study 依赖或对 sibling 的修改。偶然发现的重复只可作为非 canonical 的未来建议，不阻止当前 Study 完成。不得因共用机制而共享研究语义。

可以使用 repository runtime、Research UI、配置、filesystem/output/serialization mechanics、外部 libraries，以及 Snapshot public application/product boundary 提供的 canonical deterministic facts。上游事实由其 canonical owner 定义；如何选择、变换和解释事实以形成 evidence 仍由当前 Study 拥有。不得重定义上游事实，或以缺失的 Snapshot capability 为由越过其 public boundary。默认写入范围是当前 Study authority 与必要的最小导航条目；缺失的上游 contract / gap 在当前 Study 中记录，随后由对应 owner reconciliation。不得顺手修改 sibling Study、既有 shared Research semantics、无关 implementation 或 generic Research framework。

| 当前任务 | 下一份 authority |
| --- | --- |
| 创建 Study、确定六个 semantic areas 与文件边界 | [Schema](SCHEMA.md) |
| 结构化意图、检查完整性或处理缺失决定 | [Review](REVIEW.md) |
| 对既有 Study 做 reconciliation、migration 或 consolidation | [Compatibility](COMPATIBILITY.md) |

创建路径为 repository / module entry → 本文件 → Schema → 新 Study `ARCHITECTURE.md` → 仅所需 specialized authority → 必需的上游 authority。Review 按需进入；Compatibility、历史 Study 与 shared Research semantics 不在默认创建路径中。
