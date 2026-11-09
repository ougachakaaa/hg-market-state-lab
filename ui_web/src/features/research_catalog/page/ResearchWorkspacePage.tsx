import { Alert, Button, Card, Descriptions, Empty, Flex, List, Skeleton, Tag, Typography } from 'antd'
import { useState } from 'react'
import type { Capability } from '../api/catalog'
import { useCatalog } from '../hooks/useCatalog'
import { localCases } from '../model/localCases'

type Selection = { kind: 'online' | 'local'; id: string } | null

function CapabilityDetails({ capability }: { capability: Capability }) {
  return <Flex vertical gap="middle">
    <Descriptions size="small" column={1} bordered items={[
      { key: 'id', label: 'Research ID', children: capability.id },
      { key: 'purpose', label: 'Purpose', children: capability.purpose },
      { key: 'status', label: 'Implementation', children: `${capability.status} · live readiness: ${capability.live_readiness}` },
      { key: 'subject', label: 'Subject', children: `${capability.subject.kind} · ${capability.subject.pattern}` },
      { key: 'example', label: 'Verified example', children: `${capability.subject.verified_example} (${capability.subject.example_name}); not a default. ${capability.subject.membership_note}` },
      { key: 'metric', label: 'Metric', children: `${capability.formula} · ${capability.unit}` },
      { key: 'time', label: 'Calendar / time', children: `${capability.calendar}; horizon: ${capability.horizon_type} ${capability.horizon_unit}; ${capability.anchor_meaning}` },
      { key: 'window', label: 'Window', children: capability.window_constraints.join('; ') },
      { key: 'inputs', label: 'Other required input', children: `metric_parameters: ${capability.metric_parameters_requirement}; ordered nonempty: ${capability.ordered_nonempty_fields.join(', ')}; unique: ${capability.unique_fields.join(', ')}; on_job_failure: ${capability.on_job_failure_values.join(' / ')}` },
      { key: 'methods', label: 'Results', children: capability.analysis_methods.map(method => method.method === 'quantile'
        ? `${method.method}: ${method.required_parameters.join(', ')}; ${method.estimator}; ${method.coordinates}`
        : `${method.method}: ${method.required_parameters.join(', ')}; ${method.bins}; ${method.unit}`).join('; ') },
      { key: 'outcomes', label: 'Outcome meanings', children: capability.status_semantics.join('; ') },
      { key: 'bounds', label: 'Bounds', children: capability.bounds },
      { key: 'access', label: 'Available entry', children: 'Authenticated GET /research/capabilities; Python ResearchPlan / preview_plan / execute_batch and HTTP preview / execute require explicit plans. No Web execution form.' },
    ]} />
    <Alert type="info" title="Availability" description="The published descriptor does not probe providers, credentials or caches. Supported implementation does not guarantee a live research run." showIcon />
    <Typography.Text type="secondary">{capability.limitations.join(' ')}</Typography.Text>
  </Flex>
}

export default function ResearchWorkspacePage({ openExplorer }: { openExplorer: () => void }) {
  const catalog = useCatalog()
  const [selection, setSelection] = useState<Selection>(null)
  const selectedLocal = selection?.kind === 'local' ? localCases.find(item => item.id === selection.id) : undefined
  const selectedOnline = selection?.kind === 'online' && catalog.selectedId === selection.id
    && catalog.list.status === 'success' && catalog.list.data.some(item => item.id === selection.id)

  return <Flex vertical gap="large">
    <Flex vertical gap={0}>
      <Typography.Title level={2} style={{ margin: 0 }}>Research Workspace</Typography.Title>
      <Typography.Paragraph type="secondary">Discover published research, local cases and existing results. This workspace reads descriptions; it does not run research.</Typography.Paragraph>
    </Flex>

    <Card title="Research Catalog">
      <Flex vertical gap="large">
        <section aria-label="Available online">
          <Typography.Title level={4}>Available Online</Typography.Title>
          <Typography.Paragraph type="secondary">Authenticated capability discovery is available. Web execution and live data readiness are separate.</Typography.Paragraph>
          {catalog.list.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
          {catalog.list.status === 'error' && <Alert type="error" title="Capability catalog unavailable" description="The online list could not be loaded." action={<Button onClick={catalog.retryList}>Retry catalog</Button>} showIcon />}
          {catalog.list.status === 'success' && (catalog.list.data.length === 0
            ? <Empty description="No published online capabilities." />
            : <List dataSource={catalog.list.data} renderItem={item => <List.Item actions={[
              <Button key="details" onClick={() => { setSelection({ kind: 'online', id: item.id }); catalog.select(item.id) }}>View details</Button>,
            ]}>
              <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>Online discovery</Tag></Flex>}
                description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}</>} />
            </List.Item>} />)}
        </section>
        <section aria-label="Local and offline">
          <Typography.Title level={4}>Local / Offline</Typography.Title>
          <List dataSource={[...localCases]} renderItem={item => <List.Item actions={[
            <Button key="details" onClick={() => { catalog.clearDetail(); setSelection({ kind: 'local', id: item.id }) }}>View details</Button>,
          ]}>
            <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>{item.readiness}</Tag>{item.planned && <Tag>{item.planned}</Tag>}</Flex>}
              description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}</>} />
          </List.Item>} />
        </section>
      </Flex>
    </Card>

    {(selectedLocal || selectedOnline) && <Card title="Selected Research Details">
      {selectedLocal && <Flex vertical gap="middle">
        <Descriptions size="small" column={1} bordered items={[
          { key: 'id', label: 'Research ID', children: selectedLocal.id },
          { key: 'purpose', label: 'Purpose', children: selectedLocal.purpose },
          { key: 'readiness', label: 'Implementation', children: selectedLocal.readiness },
          { key: 'planned', label: 'Online application', children: selectedLocal.planned ?? 'No online application published.' },
          { key: 'scope', label: 'Supported scope / inputs', children: selectedLocal.scope },
          { key: 'output', label: 'Results', children: selectedLocal.output },
          { key: 'access', label: 'Available entry', children: selectedLocal.access },
        ]} />
        <Alert type="info" title="Availability" description={selectedLocal.note} showIcon />
      </Flex>}
      {selectedOnline && catalog.detail.status === 'loading' && <Skeleton active paragraph={{ rows: 5 }} />}
      {selectedOnline && catalog.detail.status === 'error' && <Alert type="error" title="Capability detail unavailable" description="The selected description could not be loaded." action={<Button onClick={catalog.retryDetail}>Retry detail</Button>} showIcon />}
      {selectedOnline && catalog.detail.status === 'success' && (catalog.detail.data.id === selection.id
        ? <CapabilityDetails capability={catalog.detail.data} />
        : <Alert type="error" title="Capability identity mismatch" showIcon />)}
    </Card>}

    <Card title="Research Results">
      <Flex vertical gap="small" align="start">
        <Typography.Text type="secondary">Open existing Research Publications, analyses, evidence and views.</Typography.Text>
        <Button type="primary" onClick={openExplorer}>Open Research Explorer</Button>
      </Flex>
    </Card>
  </Flex>
}
