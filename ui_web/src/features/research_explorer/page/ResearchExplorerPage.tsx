import { Alert, Button, Card, Collapse, Descriptions, Flex, List, Skeleton, Space, Table, Tag, Typography } from 'antd'
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
  return <section aria-label={title}><Typography.Title level={5}>{title}</Typography.Title><Descriptions size="small" column={{ xs: 1, lg: 2 }} items={Object.entries(data).map(([key, v]) => ({ key, label: ({ status: '发布状态', metric: '指标', metric_parameters: '指标参数', subjects: '标的', horizons: '时间跨度', inclusive_windows: '日期窗口（含首尾）', analysis_requests: '声明的分析请求', on_job_failure: 'Job 失败策略', jobs: 'Jobs 数量', analyses: 'Analyses 数量' } as Record<string, string>)[key] ?? key, children: <span style={{ overflowWrap: 'anywhere', whiteSpace: 'pre-wrap' }}>{Array.isArray(v) ? v.map((item, index) => <div key={index}>{value(item)}</div>) : value(v)}</span> }))} /></section>
}
export function AnalysisDetails({ analysis }: { analysis: Analysis }) {
  const result = analysis.result
  const coverage = analysis.coverage
  return <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
    <Typography.Text>实际结果状态：{analysis.outcome}{analysis.reason ? ` — ${analysis.reason}` : ''}</Typography.Text>
    {result && <>
      <Facts title="原始统计结果" data={{ method: result.method, sample_count: result.sample_count, unit: result.unit, ...(result.method === 'quantile' ? { estimator: result.estimator } : {}) }} />
      {result.method === 'quantile' ? <Table size="small" pagination={false} rowKey="key" dataSource={result.points_and_values.map(([probability, resultValue], key) => ({ key, probability, resultValue }))} columns={[{ title: '概率 Probability', dataIndex: 'probability' }, { title: '数值 Value', dataIndex: 'resultValue' }]} /> : <Table size="small" pagination={false} rowKey="label" dataSource={[
        { label: 'Underflow', left: '−∞', right: value(result.edges[0]), left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.underflow_count, frequency: result.underflow_frequency },
        ...result.bins.map((bin, i) => ({ ...bin, label: `Bin ${i + 1}`, left: value(bin.left), right: value(bin.right), left_inclusive: value(bin.left_inclusive), right_inclusive: value(bin.right_inclusive) })),
        { label: 'Overflow', left: value(result.edges.at(-1)), right: '+∞', left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.overflow_count, frequency: result.overflow_frequency },
      ]} columns={['label', 'left', 'right', 'left_inclusive', 'right_inclusive', 'count', 'frequency'].map(field => ({ title: ({ label: '区间', left: '左边界', right: '右边界', left_inclusive: '包含左边界', right_inclusive: '包含右边界', count: '计数 Count', frequency: '频率 Frequency' } as Record<string, string>)[field], dataIndex: field }))} scroll={{ x: 820 }} />}
    </>}
    {coverage ? <>
      <Facts title="观察总体与覆盖（原始比例）" data={{ candidate_count: coverage.candidate_count, eligible_count: coverage.eligible_count, unavailable_count: coverage.unavailable_count, excluded_count: coverage.excluded_count, observation_coverage: coverage.observation_coverage, unavailable_ratio: coverage.unavailable_ratio, excluded_ratio: coverage.excluded_ratio }} />
      <Collapse items={[{ key: 'evidence', label: '展开覆盖与来源证据', children: <Flex vertical gap="middle">{(['overall', 'warm_up', 'sample'] as const).map(name => <Facts key={name} title={`Market fact coverage — ${name}`} data={coverage.market_facts[name]} />)}
      <Facts title="来源与输入证据 Provenance" data={{ observation_unit: coverage.observation_unit, input_profile: coverage.input_profile, input_fingerprint: coverage.input_fingerprint }} /></Flex> }]} />
    </> : <Alert type="info" title="Coverage 不可用" description="未发布观察覆盖；不表示覆盖完整或研究成功。" />}
  </Space>
}
export default function ResearchExplorerPage() {
  const e = useExplorer()
  const manifest = e.manifest.status === 'success' ? e.manifest.data : null
  const selected = manifest?.analyses.find(a => a.analysis_id === e.analysis)
  let unsupported = false
  if (e.chart.status === 'success') { try { chartViewToPlotly(e.chart.data) } catch (error) { if (error instanceof UnsupportedLayerError) unsupported = true; else throw error } }
  return <Flex vertical gap="large" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
    <header><Typography.Title level={2} style={{ margin: 0 }}>研究结果浏览</Typography.Title><Typography.Paragraph type="secondary">逐层查看 Publication → Job → Analysis → ChartView。声明范围、执行状态与统计证据分别保留。</Typography.Paragraph></header>
    <Card title="Publications" extra={<Button onClick={e.retryList}>刷新</Button>}>
      {e.list.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {e.list.status === 'error' && <Space orientation="vertical"><ErrorState context="Publication 列表" error={e.list.error} retry={e.retryList} />{e.page > 0 && <Button onClick={e.previous}>上一页</Button>}</Space>}
      {e.list.status === 'success' && <>
        {e.list.data.data.length === 0 ? <Typography.Text>{e.page === 0 ? 'Publication Store 为空。' : '此页没有 Publication。'}</Typography.Text> : <List rowKey="publication_id" dataSource={e.list.data.data} renderItem={item => <List.Item actions={[<Button key="open" aria-pressed={e.publication === item.publication_id} type={e.publication === item.publication_id ? 'primary' : 'default'} onClick={() => e.selectPublication(item.publication_id)}>选择</Button>]}><List.Item.Meta title={item.publication_id} description={<Tag>发布状态：{item.status}</Tag>} /></List.Item>} />}
        <Flex gap="small" align="center" wrap><Typography.Text type="secondary">当前第 {e.page + 1} 页</Typography.Text><Button disabled={e.page === 0} onClick={e.previous}>上一页</Button><Button disabled={e.list.data.next_cursor === null} onClick={() => e.next(e.list.status === 'success' ? e.list.data.next_cursor! : '')}>下一页</Button></Flex>
      </>}
    </Card>
    {e.publication && <Card title="所选 Publication" extra={<Button onClick={() => e.selectPublication(null)}>返回列表</Button>}>
      {e.manifest.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {e.manifest.status === 'error' && <ErrorState context="Publication" error={e.manifest.error} retry={e.retryManifest} />}
      {manifest && <Flex vertical gap="middle">
        <Typography.Text code>{manifest.publication_id}</Typography.Text>
        <Facts title="声明的 Research scope" data={{ status: manifest.status, metric: manifest.scope.metric, metric_parameters: manifest.scope.metric_parameters, subjects: manifest.scope.subjects, horizons: manifest.scope.horizons, inclusive_windows: manifest.scope.windows, analysis_requests: manifest.scope.analysis_requests, on_job_failure: manifest.scope.on_job_failure, jobs: manifest.jobs.length, analyses: manifest.analyses.length }} />
        <Collapse items={[{ key: 'source', label: 'Publication 来源证据', children: <><Typography.Paragraph type="secondary">摘要与输入指纹用于标识证据，不证明市场数据真实性。</Typography.Paragraph><Facts title="来源元数据" data={{ schema_version: manifest.schema_version, context: manifest.context, source_sha256: manifest.source.sha256, source_size: manifest.source.size }} /></> }]} />
        <Typography.Title level={4}>Jobs 与 Analysis</Typography.Title>
        {manifest.jobs.map((job, index) => <Card key={JSON.stringify(job.job_identity)} size="small" title={`Job ${index + 1} — ${job.status}`}>
          <Flex gap="small" wrap><Typography.Text strong>{job.job_identity.subject}</Typography.Text><Typography.Text type="secondary">H = {job.job_identity.horizon} {job.job_identity.horizon_unit} · {job.job_identity.start_date} → {job.job_identity.end_date}</Typography.Text></Flex>
          <Collapse ghost size="small" items={[{ key: 'identity', label: '完整 Job 身份', children: <Facts title="Job 身份" data={job.job_identity} /> }]} />
          <List rowKey={id => id} dataSource={job.analyses} renderItem={id => { const item = manifest.analyses.find(a => a.analysis_id === id); return item ? <List.Item actions={[<Button key="select" aria-pressed={e.analysis === id} type={e.analysis === id ? 'primary' : 'default'} onClick={() => e.selectAnalysis(id)}>选择 Analysis</Button>]}><List.Item.Meta title={`${item.request_id} — ${item.status}`} description={<span>Analysis ID: {id}<br />方法与参数： {JSON.stringify(item.spec)}<br />已发布 Views： {item.views.map(v => `${v.measure}: ${v.view_id}`).join(', ') || '无'}</span>} /></List.Item> : <List.Item>关联 Analysis 不可用：{id}</List.Item> }} />
        </Card>)}
      </Flex>}
    </Card>}
    {e.analysis && <Card title="所选 Analysis" extra={<Button onClick={() => e.selectAnalysis(null)}>关闭 Analysis</Button>}>
      {e.result.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {e.result.status === 'error' && <ErrorState context="Analysis" error={e.result.error} retry={e.retryResult} />}
      {e.result.status === 'success' && <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
        <Typography.Text code>{e.analysis}</Typography.Text>
        <AnalysisDetails analysis={e.result.data} />
        <Typography.Title level={4}>ChartViews</Typography.Title>
        <Typography.Text type="secondary">选择一个已发布 View 后读取图表。</Typography.Text>
        {selected?.views.length ? <Space wrap>{selected.views.map(v => <Button key={v.view_id} title={v.view_id} aria-pressed={e.view === v.view_id} type={e.view === v.view_id ? 'primary' : 'default'} onClick={() => e.setView(v.view_id)}>{v.measure}</Button>)}</Space> : <Alert type="info" title="没有可用的 ChartView" />}
        {e.view && <Typography.Text code>View ID: {e.view}</Typography.Text>}
        {e.chart.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
        {e.chart.status === 'error' && <ErrorState context="View" error={e.chart.error} retry={e.retryChart} />}
        {e.chart.status === 'success' && (unsupported ? <Alert type="warning" title="当前渲染器不支持此 View。" /> : <div style={{ height: 450, minWidth: 0, width: '100%' }}><ChartView view={e.chart.data} /></div>)}
      </Space>}
    </Card>}
  </Flex>
}
