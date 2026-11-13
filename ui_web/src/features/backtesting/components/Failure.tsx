import { Alert, Collapse, Descriptions, Typography } from 'antd'
import type { Run } from '../api/backtesting'
import { failurePresentation } from '../model/presentation'

export function Failure({ status, failure, runId }: { status: string; failure?: Run['failure']; runId?: string }) {
  const message = failurePresentation(status, failure)
  return <>
    <Alert type="error" title={message.title} description={<><Typography.Paragraph>{message.description}</Typography.Paragraph><Typography.Paragraph>{message.action}</Typography.Paragraph></>} />
    <Collapse items={[{ key: 'details', label: '技术详情', children: <Descriptions column={1} items={[
      { key: 'stage', label: 'Stage', children: failure?.stage ?? '—' },
      { key: 'category', label: 'Category', children: failure?.category ?? '—' },
      { key: 'dependency', label: 'Dependency', children: failure?.dependency ?? '—' },
      { key: 'reason', label: 'Reason', children: failure?.reason ?? '—' },
      ...(runId ? [{ key: 'run', label: 'Run ID', children: runId }] : []),
    ]} /> }]} />
  </>
}
