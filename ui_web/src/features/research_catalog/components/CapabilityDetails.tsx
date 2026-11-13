import { Alert, Collapse, Descriptions, Flex, Typography } from 'antd'
import type { Capability } from '../api/validateCatalog'
import { STATIC_CATALOG_DISCLOSURE, type ResearchOverviewMode } from '../model/catalogPresentation'

export function CapabilityDetails({ capability, mode }: {
  capability: Capability
  mode: ResearchOverviewMode
}) {
  const staticMode = mode === 'static'
  return <Flex vertical gap="middle">
    {staticMode && <Typography.Paragraph type="secondary" role="note" style={{ marginBottom: 0 }}>{STATIC_CATALOG_DISCLOSURE}</Typography.Paragraph>}
    <Descriptions title="身份与用途" size="small" column={1} items={[
      { key: 'id', label: '研究 ID', children: capability.id },
      { key: 'purpose', label: '用途', children: capability.purpose },
      { key: 'status', label: '实现与可用性', children: `${capability.status} · live readiness: ${capability.live_readiness}` },
    ]} />
    <Descriptions title="范围、指标与时间" size="small" column={{ xs: 1, lg: 2 }} items={[
      { key: 'subject', label: '支持标的', children: `${capability.subject.kind} · ${capability.subject.pattern}` },
      { key: 'example', label: '已验证示例', children: `${capability.subject.verified_example} (${capability.subject.example_name}); 不是默认值。 ${capability.subject.membership_note}` },
      { key: 'metric', label: '指标与单位', children: `${capability.formula} · ${capability.unit}` },
      { key: 'time', label: '日历与时间跨度', children: `${capability.calendar}; horizon: ${capability.horizon_type} ${capability.horizon_unit}; ${capability.anchor_meaning}` },
      { key: 'window', label: '窗口约束', children: capability.window_constraints.join('; ') },
      { key: 'bounds', label: '边界', children: capability.bounds },
    ]} />
    <Descriptions title="输入要求与分析方法" size="small" column={1} items={[
      { key: 'inputs', label: '输入要求', children: `metric_parameters: ${capability.metric_parameters_requirement}; ordered nonempty: ${capability.ordered_nonempty_fields.join(', ')}; unique: ${capability.unique_fields.join(', ')}; on_job_failure: ${capability.on_job_failure_values.join(' / ')}` },
      ...capability.analysis_methods.map(method => ({ key: method.method, label: method.method, children: method.method === 'quantile'
        ? `${method.required_parameters.join(', ')}; estimator: ${method.estimator}; ${method.coordinates}`
        : `${method.required_parameters.join(', ')}; ${method.bins}; ${method.unit}; ${method.coordinates}` })),
      { key: 'outcomes', label: '结果状态含义', children: capability.status_semantics.join('; ') },
      { key: 'access', label: '访问路径', children: staticMode
        ? '认证 GET /research/capabilities；Python ResearchPlan / preview_plan / execute_batch 和 HTTP preview / execute 需要显式计划。此处无 Web 执行表单。以上为正式产品访问说明；静态演示不执行认证 GET、Python 或研究执行。'
        : '认证 GET /research/capabilities；Python ResearchPlan / preview_plan / execute_batch 和 HTTP preview / execute 需要显式计划。此处无 Web 执行表单。' },
    ]} />
    <Alert type="info" title="可用性说明" description={staticMode
      ? '发布的描述不探测 Provider、凭据或缓存。supported 与 live_readiness 保持发布原值，不保证实际研究可以运行。静态演示只读取嵌入描述。'
      : '发布的描述不探测 Provider、凭据或缓存。supported 不保证实际研究可以运行。'} showIcon />
    <Typography.Text type="secondary">{capability.limitations.join(' ')}</Typography.Text>
    <Collapse items={[{ key: 'descriptor', label: '完整能力描述（原始字段）', children: <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', margin: 0 }}>{JSON.stringify(capability, null, 2)}</pre> }]} />
  </Flex>
}
