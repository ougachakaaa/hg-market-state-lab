import { Alert, Button, Card, Collapse, Descriptions, Empty, Flex, List, Skeleton, Tag, Typography } from 'antd'
import { useState } from 'react'
import type { Capability } from '../api/catalog'
import { useCatalog } from '../hooks/useCatalog'
import { localCases } from '../model/localCases'

type Selection = { kind: 'online' | 'local'; id: string } | null

function CapabilityDetails({ capability }: { capability: Capability }) {
  return <Flex vertical gap="middle">
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
      { key: 'access', label: '访问路径', children: '认证 GET /research/capabilities；Python ResearchPlan / preview_plan / execute_batch 和 HTTP preview / execute 需要显式计划。此处无 Web 执行表单。' },
    ]} />
    <Alert type="info" title="可用性说明" description="发布的描述不探测 Provider、凭据或缓存。supported 不保证实际研究可以运行。" showIcon />
    <Typography.Text type="secondary">{capability.limitations.join(' ')}</Typography.Text>
    <Collapse items={[{ key: 'descriptor', label: '完整能力描述（原始字段）', children: <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', margin: 0 }}>{JSON.stringify(capability, null, 2)}</pre> }]} />
  </Flex>
}

export default function ResearchWorkspacePage({ openExplorer, openFuturesBasis }: { openExplorer: () => void; openFuturesBasis: () => void }) {
  const catalog = useCatalog()
  const [selection, setSelection] = useState<Selection>(null)
  const selectedLocal = selection?.kind === 'local' ? localCases.find(item => item.id === selection.id) : undefined
  const selectedOnline = selection?.kind === 'online' && catalog.selectedId === selection.id
    && catalog.list.status === 'success' && catalog.list.data.some(item => item.id === selection.id)

  return <Flex vertical gap="large" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
    <Flex vertical gap={0}>
      <Typography.Title level={2} style={{ margin: 0 }}>研究工作台</Typography.Title>
      <Typography.Paragraph type="secondary">发现已发布能力、本地案例与已有研究结果。本工作台只读，不执行研究。</Typography.Paragraph>
    </Flex>

    <Card title="研究发现">
      <Flex vertical gap="large">
        <section aria-label="在线能力发现">
          <Typography.Title level={4}>在线能力发现</Typography.Title>
          <Typography.Paragraph type="secondary">通过认证接口发现能力。实现支持不代表 Provider、凭据或缓存已就绪。</Typography.Paragraph>
          {catalog.list.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
          {catalog.list.status === 'error' && <Alert type="error" title="在线能力目录暂不可用" description="未能读取在线列表；本地案例仍可查看。" action={<Button onClick={catalog.retryList}>重试目录</Button>} showIcon />}
          {catalog.list.status === 'success' && (catalog.list.data.length === 0
            ? <Empty description="暂无已发布的在线能力。" />
            : <List rowKey="id" dataSource={catalog.list.data} renderItem={item => <List.Item actions={[
              <Button key="details" aria-pressed={selection?.kind === 'online' && selection.id === item.id} type={selection?.kind === 'online' && selection.id === item.id ? 'primary' : 'default'} onClick={() => { setSelection({ kind: 'online', id: item.id }); catalog.select(item.id) }}>查看详情</Button>,
            ]}>
              <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>在线描述发现</Tag><Tag>实现：{item.status}</Tag><Tag>live readiness: {item.live_readiness}</Tag></Flex>}
                description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}<br />访问路径：认证 HTTP 描述读取</>} />
            </List.Item>} />)}
        </section>
        <section aria-label="本地研究与离线工作流">
          <Typography.Title level={4}>本地研究与离线工作流</Typography.Title>
          <List rowKey="id" dataSource={[...localCases]} renderItem={item => <List.Item actions={[
            <Button key="details" aria-pressed={selection?.kind === 'local' && selection.id === item.id} type={selection?.kind === 'local' && selection.id === item.id ? 'primary' : 'default'} onClick={() => { catalog.clearDetail(); setSelection({ kind: 'local', id: item.id }) }}>查看详情</Button>,
          ]}>
            <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>{item.readiness}</Tag>{item.planned && <Tag>{item.planned}</Tag>}</Flex>}
              description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}<br />访问路径：{item.id === 'price_segmentation_v1' ? '本地 Python' : '独立在线页面 / 本地离线报告'}</>} />
          </List.Item>} />
        </section>
      </Flex>
    </Card>

    {(selectedLocal || selectedOnline) && <Card title="所选研究详情" role="region" aria-label="所选研究详情">
      {selectedLocal && <Flex vertical gap="middle">
        <Descriptions size="small" column={{ xs: 1, lg: 2 }} items={[
          { key: 'id', label: '研究 ID', children: selectedLocal.id },
          { key: 'purpose', label: '用途', children: selectedLocal.purpose },
          { key: 'readiness', label: '实现与可用性', children: selectedLocal.readiness },
          { key: 'planned', label: '在线应用', children: selectedLocal.planned ?? '未发布在线应用。' },
          { key: 'scope', label: '支持范围与输入', children: selectedLocal.scope },
          { key: 'output', label: '分析结果', children: selectedLocal.output },
          { key: 'access', label: '访问路径', children: selectedLocal.access },
        ]} />
        <Alert type="info" title="可用性说明" description={selectedLocal.note} showIcon />
        {selectedLocal.id === 'futures_basis_v1' && <Button type="primary" onClick={openFuturesBasis}>打开 Futures Basis Research</Button>}
      </Flex>}
      {selectedOnline && catalog.detail.status === 'loading' && <Skeleton active paragraph={{ rows: 5 }} />}
      {selectedOnline && catalog.detail.status === 'error' && <Alert type="error" title="能力详情暂不可用" description="未能读取所选能力描述。" action={<Button onClick={catalog.retryDetail}>重试详情</Button>} showIcon />}
      {selectedOnline && catalog.detail.status === 'success' && (catalog.detail.data.id === selection.id
        ? <CapabilityDetails capability={catalog.detail.data} />
        : <Alert type="error" title="能力身份不匹配" showIcon />)}
    </Card>}

    <Card title="已有研究结果">
      <Flex vertical gap="small" align="start">
        <Typography.Text type="secondary">浏览已发布的 Publications、Analyses、研究证据和 ChartViews。</Typography.Text>
        <Button type="primary" onClick={openExplorer}>打开研究结果浏览</Button>
      </Flex>
    </Card>
  </Flex>
}
