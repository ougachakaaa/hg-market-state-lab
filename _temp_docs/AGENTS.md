# `_temp_docs/` — 临时文档目录

本目录仅用于临时存放超长设计文档与任务过程稿（`.gitignore` 中已忽略 `_temp_docs/**`）。

## 规则

* 本目录内容不具备 authority 地位，不参与根或任何 module / specialized authority 的导航链；正式入口见根 `ARCHITECTURE.md`。
* 除非当前任务显式引用或提到本目录下的某个具体文档，Agent 默认跳过本目录：不读取、不引用、不作为参考或实现依据。
* 本目录中的文档、数据与结论都是服务于某个具体任务的临时材料，可能已过期、片面或与当前 authority 不一致。
* 如需将其中内容固化为项目事实，必须先与当前 authority 进行 reconciliation，并写入 narrowest canonical authority，而不是继续引用本目录。
