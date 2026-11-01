import { Alert, Button, Card, Descriptions, Flex, List, Space, Spin, Table, Tag, Typography } from 'antd'
import { ChartView, chartViewToPlotly, UnsupportedLayerError } from '../../../shared/visualization'
import { ResearchError, type Analysis, type FailureKind } from '../api/research'
import { useExplorer } from '../hooks/useExplorer'

const messages: Record<FailureKind, string> = {
  invalid_request: '请求无效或游标已失效。', not_found: '未找到所选 Publication、Analysis 或 View。',
  corrupt: '已存储的内容无效或损坏。', inconsistent: 'Publication 的证据关联不一致。',
  unsupported_version: '不支持此存储版本。', response_too_large: '响应超过大小限制。',
  verification_budget_exceeded: '来源验证容量不足，请稍后手动重试。', unavailable: 'Publication 存储或来源不可用。',
  internal_error: '服务内部错误。', authentication_required: '需要登录。', invalid_credentials: '认证失败。',
  origin_forbidden: '访问被拒绝。', rate_limited: '请求过于频繁。', network: '无法连接服务。',
  invalid_response: '服务返回了无法识别的响应。', invalid_view: 'ChartView 格式无效或不兼容。',
}
function ErrorState({ error, retry, context }: { error: unknown; retry: () => void; context: string }) {
  return <Alert type="error" showIcon title={error instanceof ResearchError && error.kind === 'not_found' ? `未找到所选 ${context}。` : error instanceof ResearchError ? messages[error.kind] : '请求失败。'} action={<Button onClick={retry}>重试</Button>} />
}
const value = (v: unknown) => v === null || v === undefined ? 'N/A' : typeof v === 'object' ? JSON.stringify(v) : String(v)
function Facts({ title, data }: { title: string; data: object }) {
  return <Card size="small" title={title}><Descriptions size="small" column={2} bordered items={Object.entries(data).map(([key, v]) => ({ key, label: key, children: value(v) }))} /></Card>
}
export function AnalysisDetails({ analysis }: { analysis: Analysis }) {
  const result = analysis.result
  const coverage = analysis.coverage
  return <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
    <Typography.Text>实际结果状态：{analysis.outcome}{analysis.reason ? ` — ${analysis.reason}` : ''}</Typography.Text>
    {result && <>
      <Facts title="原始统计结果" data={{ method: result.method, sample_count: result.sample_count, unit: result.unit, ...(result.method === 'quantile' ? { estimator: result.estimator } : {}) }} />
      {result.method === 'quantile' ? <Table size="small" pagination={false} rowKey="key" dataSource={result.points_and_values.map(([probability, resultValue], key) => ({ key, probability, resultValue }))} columns={[{ title: 'Probability', dataIndex: 'probability' }, { title: 'Value', dataIndex: 'resultValue' }]} /> : <Table size="small" pagination={false} rowKey="label" dataSource={[
        { label: 'Underflow', left: '−∞', right: value(result.edges[0]), left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.underflow_count, frequency: result.underflow_frequency },
        ...result.bins.map((bin, i) => ({ ...bin, label: `Bin ${i + 1}`, left: value(bin.left), right: value(bin.right), left_inclusive: value(bin.left_inclusive), right_inclusive: value(bin.right_inclusive) })),
        { label: 'Overflow', left: value(result.edges.at(-1)), right: '+∞', left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.overflow_count, frequency: result.overflow_frequency },
      ]} columns={['label', 'left', 'right', 'left_inclusive', 'right_inclusive', 'count', 'frequency'].map(field => ({ title: field, dataIndex: field }))} scroll={{ x: true }} />}
    </>}
    {coverage ? <>
      <Facts title="Observation population and coverage (原始比例)" data={{ candidate_count: coverage.candidate_count, eligible_count: coverage.eligible_count, unavailable_count: coverage.unavailable_count, excluded_count: coverage.excluded_count, observation_coverage: coverage.observation_coverage, unavailable_ratio: coverage.unavailable_ratio, excluded_ratio: coverage.excluded_ratio }} />
      {(['overall', 'warm_up', 'sample'] as const).map(name => <Facts key={name} title={`Market fact coverage — ${name}`} data={coverage.market_facts[name]} />)}
      <Facts title="Provenance" data={{ observation_unit: coverage.observation_unit, input_profile: coverage.input_profile, input_fingerprint: coverage.input_fingerprint }} />
    </> : <Alert type="info" title="Coverage unavailable" />}
  </Space>
}
export default function ResearchExplorerPage() {
  const e = useExplorer()
  const manifest = e.manifest.status === 'success' ? e.manifest.data : null
  const selected = manifest?.analyses.find(a => a.analysis_id === e.analysis)
  let unsupported = false
  if (e.chart.status === 'success') { try { chartViewToPlotly(e.chart.data) } catch (error) { if (error instanceof UnsupportedLayerError) unsupported = true; else throw error } }
  return <Space orientation="vertical" size="large" style={{ width: '100%' }}>
    <Typography.Title level={2}>Research Explorer</Typography.Title>
    <Card title="Publications" extra={<Button onClick={e.retryList}>刷新</Button>}>
      {e.list.status === 'loading' && <Spin />}
      {e.list.status === 'error' && <ErrorState context="Publication 列表" error={e.list.error} retry={e.retryList} />}
      {e.list.status === 'success' && <>
        {e.list.data.data.length === 0 ? <Typography.Text>{e.page === 0 ? 'Publication Store 为空。' : '此页没有 Publication。'}</Typography.Text> : <List dataSource={e.list.data.data} renderItem={item => <List.Item actions={[<Button key="open" onClick={() => e.selectPublication(item.publication_id)}>选择</Button>]}><List.Item.Meta title={item.publication_id} description={<Tag>{item.status}</Tag>} /></List.Item>} />}
        <Flex gap="small"><Button disabled={e.page === 0} onClick={e.previous}>上一页</Button><Button disabled={e.list.data.next_cursor === null} onClick={() => e.next(e.list.status === 'success' ? e.list.data.next_cursor! : '')}>下一页</Button></Flex>
      </>}
    </Card>
    {e.publication && <Card title={`Publication ${e.publication}`} extra={<Button onClick={() => e.selectPublication(null)}>返回列表</Button>}>
      {e.manifest.status === 'loading' && <Spin />}
      {e.manifest.status === 'error' && <ErrorState context="Publication" error={e.manifest.error} retry={e.retryManifest} />}
      {manifest && <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
        <Facts title="声明的 Research scope" data={{ status: manifest.status, metric: manifest.scope.metric, metric_parameters: manifest.scope.metric_parameters, subjects: manifest.scope.subjects, horizons: manifest.scope.horizons, inclusive_windows: manifest.scope.windows, analysis_requests: manifest.scope.analysis_requests, on_job_failure: manifest.scope.on_job_failure, source_sha256: manifest.source.sha256, source_size: manifest.source.size, jobs: manifest.jobs.length, analyses: manifest.analyses.length }} />
        {manifest.jobs.map((job, index) => <Card key={JSON.stringify(job.job_identity)} size="small" title={`Job ${index + 1} — ${job.status}`}>
          <Facts title="Job identity" data={job.job_identity} />
          <List dataSource={job.analyses} renderItem={id => { const item = manifest.analyses.find(a => a.analysis_id === id); return item ? <List.Item actions={[<Button key="select" onClick={() => e.selectAnalysis(id)}>选择 Analysis</Button>]}><List.Item.Meta title={`${item.request_id} — ${item.status}`} description={<span>Analysis ID: {id}<br />Method / parameters: {JSON.stringify(item.spec)}<br />Views: {item.views.map(v => `${v.measure}: ${v.view_id}`).join(', ') || '无'}</span>} /></List.Item> : <List.Item>关联 Analysis 不可用：{id}</List.Item> }} />
        </Card>)}
      </Space>}
    </Card>}
    {e.analysis && <Card title={`Analysis ${e.analysis}`} extra={<Button onClick={() => e.selectAnalysis(null)}>关闭 Analysis</Button>}>
      {e.result.status === 'loading' && <Spin />}
      {e.result.status === 'error' && <ErrorState context="Analysis" error={e.result.error} retry={e.retryResult} />}
      {e.result.status === 'success' && <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
        <AnalysisDetails analysis={e.result.data} />
        {selected?.views.length ? <Space wrap>{selected.views.map(v => <Button key={v.view_id} type={e.view === v.view_id ? 'primary' : 'default'} onClick={() => e.setView(v.view_id)}>{v.measure}</Button>)}</Space> : <Alert type="info" title="没有可用的 ChartView" />}
        {e.chart.status === 'loading' && <Spin />}
        {e.chart.status === 'error' && <ErrorState context="View" error={e.chart.error} retry={e.retryChart} />}
        {e.chart.status === 'success' && (unsupported ? <Alert type="warning" title="当前渲染器不支持此 View。" /> : <div style={{ height: 450 }}><ChartView view={e.chart.data} /></div>)}
      </Space>}
    </Card>}
  </Space>
}
