# DataLake diagnostics authority

本文件拥有 DataLake operational diagnostics；继承 [模块边界](ARCHITECTURE.md) 与 [Application contract](APPLICATION.md)。日志不改变 public result、coverage、completeness、事务或 failure taxonomy。

使用标准 Python logging 的 `data_lake` logger hierarchy。Library 不安装 handler、不默认写文件；consumer 决定日志 delivery。Provider DEBUG events 包含 endpoint、allowlisted semantic request selectors、分页 offset/limit、启动等待、耗时和成功行数；失败 WARNING event 包含安全错误分类和 numeric code。禁止记录 credential、请求 body、任意 provider message、response dump 或 exception traceback。未知请求参数不写日志。

Kernel INFO events 包含 Dataset、ensure 目标数、缓存跳过数、周期性进度及最终计数；单元失败 WARNING 包含 semantic identity、safe code/reason，不包含 SQLite/internal IDs。Source daily numeric normalization / required-field failure 应指出字段名、合约/指数与日期和安全的校验失败类型；不输出 arbitrary raw values。字段允许缺席的业务条件仍由 owning FACTS authority 唯一拥有。

CLI 日志选项、默认级别、file delivery 与 handler 生命周期由 [lab authority](../ui_cli/ARCHITECTURE.md) 拥有。日志不能以无失败替代 coverage.complete 验收。
