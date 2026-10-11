# DataLake Dataset Composition authority

本文件拥有自治 Dataset 接入 Shared Kernel 的公共 Composition Contract，继承 [模块架构](ARCHITECTURE.md)。Domain primitives 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md)，三个 Use Cases / public result / failures 见 [APPLICATION.md](APPLICATION.md)，两个 Outbound capability contracts 见 [PORTS.md](PORTS.md)。具体 Dataset 的领域特化与角色绑定从 [DATASETS.md](DATASETS.md) 进入其 ARCHITECTURE.md；不要求阅读 sibling internals。

## 1. 六个核心接入角色

Dataset 是自治领域边界，不是一个 Use Case。它定义事实全集、自然身份、标准化、完整性与 Export 语义；Composition Root 将下列 **四个领域策略 + 两个 Outbound Ports** 接入 Kernel Application。

| 接入角色 | Semantic owner | 输入 → 输出 / 责任 |
| --- | --- | --- |
| Target Planner | Dataset Domain | 合法 Dataset request 的 Scope + Window，以及必要的已固定 prerequisite view → 确定的目标 FetchUnit identities；不创建 rows、不根据行情缺行缩小目标 |
| Source Port / Adapter | Kernel 定义 Port；Dataset 拥有 Adapter | selected unit batch → 逐 unit 事实输入 / 安全失败；Dataset 决定 Source mapping，Provider 执行外部请求，详见 PORTS.md |
| Normalizer | Dataset Domain | 一个目标 Unit + 对应 Source facts / 合法 metadata basis → canonical UnitRecords（Records、关联 Instruments、必要 basis）；确定性转换，不补造事实或生成分析派生值 |
| Completeness Validator | Dataset Domain | 一个 Unit + UnitRecords → 通过或明确失败；定义 cardinality、自然 identity、required facts、instrument association 与 expected/observed predicate，纯验证、不补取 Source、不写库 |
| Export Projector | Dataset Domain / public view semantics | 本次 request context + 已验证 coverage + 同一 snapshot 的成功 cached facts / basis → SERVICE.md 定义的业务 Export View、ordering 与空 payload；不再次读库或访问 Source |
| Repository Port / Adapter | Kernel 定义 Port 并维护标准 SQLite Adapter；Dataset 绑定存储实例 | 明确 units / 状态操作 / 已验证 UnitRecords ↔ Dataset-local consistent snapshot / 原子提交结果；持久化机制见 PORTS.md 与 PERSISTENCE.md |

这些是责任角色，不要求每个策略各自建立 Protocol、抽象基类、类或文件，也不要求六个构造器参数。`UnitRecords` 是 Kernel 的通用事实组载体，不能内置某个 Dataset 的字段或 expected-set 解释。业务 Scope / Window 可以保留 Dataset typed objects，Kernel 仅拥有公共语义，不建立通用维度 schema。

## 2. Composition Root 与 Public Service

Composition Root 由 owning Dataset 维护，选择并绑定领域策略、Dataset Source Adapter、标准 Repository Adapter、自己的 storage context 与已授权的 Dataset Public Service dependencies。它可依赖这些具体实现；Application 本身只依赖 Domain / Ports。Root 不能通过共享实例合并两个 Dataset 的 persistence ownership。

Dataset Public Application Service 是 Composition 的产物和唯一 consumer boundary，拥有 semantic request validation、operation-specific prerequisite orchestration 与 Kernel delegation。它不是第七个接入角色，也不是 Kernel Inbound Adapter。`create_service()`、public class / request / result / view 与 errors 保持原 SERVICE.md 契约；Source、Repository、token、prefetch 和内部策略不进入 public request。

普通 factory 仅组合依赖，不能读取 credential、初始化 provider client、发起 Source I/O 或 materialize SQLite。Coverage/export 的全部调用链只读。Ensure 只有实际需要 Source I/O 才初始化相关 provider；无 selected units 时不准备自己的 Source。Prerequisite 是否需要 ensure 由 Dataset 已声明权限决定，不由 Kernel 推导。

## 3. Target planning 与 prerequisite orchestration

Public Service 先验证自己的 request，再按 APPLICATION.md 及 owning TRADING_DAYS.md 取得并固定合法 prerequisite semantic view，然后由 Target Planner 展开完整 identities，交给 Kernel Application。Planner 可在无 prerequisite 时直接解释 Scope + Window；在需要 prerequisite 时只消费已经准备好的 facts，不把 Source I/O 藏进纯领域展开。

已授权 consumer 的 ensure 可以先补齐 prerequisite，其 coverage/export 仅可读取；具体 request、exchange、调用顺序与失败由 consumer Dataset 拥有。未知 prerequisite 导致无法证明目标全集时抛 OperationError，不生成子集/零目标 Coverage，不把 prerequisite failures 编成 consumer UnitFailure。Kernel 不认识 Calendar 或其他 Dataset service，也不新增 dependency graph engine。

目标合法且固定后，Application 拥有通用 selection、状态协调、Source 编排、调用 Normalize / Validate、Repository 提交、读验证、公共计数与 Projector 调用；Dataset 不复制通用 ensure/coverage/snapshot engine。Source Request 与 FetchUnit 的关系、Source/Repository 失败责任由 PORTS.md 拥有。Success/freshness、逐 unit 原子性、export consistency、frozen basis 与 generation compatibility 继续继承各自公共 authority。

## 4. 可选执行策略与生命周期

Dataset 可提供 Batch Planner：输入 selected units，输出有限、非空且精确 partition 全部 selected units 的 batches；没有具体 batching 需要时使用 Kernel 默认分组。Batch Planner 是可选执行策略，不属于四个领域策略，也不是第三个 Outbound Port。具体 grouping / endpoint limits 归 Dataset，验证分组、调度、单 writer 与 cancellation 归 [EXECUTION.md](EXECUTION.md)。

Prefetch 是 Kernel 执行配置，不是业务 Port 或 public semantic input。Source/catalog、Completeness Validator 的 memo 与 typed projection cache 按 operation/read snapshot 限定生命周期；Composition Root 负责建立正确实例，不能复用可变的旧 operation basis。Shared Provider execution state 遵守 Provider 自己的 process/credential lifecycle，不随 Dataset operation 销毁或重置。

## 5. 目标代码职责组织

Kernel 的目标目录由模块架构锁定。Dataset 保持 `datasets/<dataset-id>/src/data_lake/datasets/<dataset-id>/` 的 co-location 与 public namespace，按实际职责组织：

- Dataset Domain：业务 Scope / Window interpretation、Target Planner、facts / metadata normalization、Completeness Validator、Export Projector；只依赖 Kernel 中立领域/结果类型与本 Dataset 语义。
- Dataset Source Adapter：provider-native requests、分页、partition、调用本 Dataset 纯领域映射；依赖 Kernel Source Port 与 Provider Infrastructure，不依赖 SQLite 或 sibling internals。
- Composition Root / Public Service：request / prerequisite 编排，绑定领域策略与具体 Adapters，委托三个 Kernel Use Cases；允许导入已授权 producer 的 public facade。
- Public models / facade：保留现有 public types、import surface、wire meaning 与 errors；对外不发布内部策略或 persistence types。

不锁定 Dataset 的机械文件模板；当前 `_models.py`、`_source.py`、`_service.py` 的名字不授予 semantic ownership。纯业务规则不能因调用 provider 或当前 colocate 于 adapter 文件而被定义为 Provider / Kernel 规则。只因一个 Dataset 存在的逻辑仍归该 Dataset；重复的 representation helper 不自动证明应抽进 Kernel。

新增或修改 Dataset 时，先在 owning authority 确认事实、六角色绑定和必要依赖权限，再实现；不得新增 DataLakeService、DatasetManager、Registry、Plugin Framework、通用依赖图或无实际职责的 Inbound Adapter。当前代码到目标职责的差距记录在 [RECONCILIATION.md](RECONCILIATION.md)，不改变以上契约。
