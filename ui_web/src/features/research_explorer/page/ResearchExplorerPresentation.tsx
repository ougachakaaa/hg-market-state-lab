import { Alert, Button, Card, Collapse, Flex, List, Skeleton, Space, Tag, Typography } from 'antd'
import { intervalLabels } from '../../../shared/format/interval'
import { ChartView, chartViewToPlotly, UnsupportedLayerError } from '../../../shared/visualization'
import { categoryLabelOptions } from '../../../shared/visualization/presentation'
import { AnalysisDetails } from '../components/AnalysisDetails'
import { ErrorState } from '../components/ErrorState'
import { Facts } from '../components/Facts'
import {
  STATIC_EXPLORER_DISCLOSURE,
  STATIC_SOURCE_NOTE,
  type ResearchExplorerController,
  type ResearchExplorerMode,
} from '../model/explorerPresentation'

export function ResearchExplorerPresentation({ controller, mode, sourceDisclosure }: {
  controller: ResearchExplorerController
  mode: ResearchExplorerMode
  sourceDisclosure?: string
}) {
  const staticMode = mode === 'static'
  const manifest = controller.manifest.status === 'success' ? controller.manifest.data : null
  const selected = controller.analysis && manifest
    ? manifest.analyses.find(item => item.analysis_id === controller.analysis) : undefined
  const result = controller.result.status === 'success' ? controller.result.data : null
  let unsupported = false
  if (controller.chart.status === 'success') {
    try { chartViewToPlotly(controller.chart.data) } catch (error) {
      if (error instanceof UnsupportedLayerError) unsupported = true
      else throw error
    }
  }
  const options = controller.chart.status === 'success' && result?.result?.method === 'interval_count' && result.result.unit === 'decimal_ratio'
    ? categoryLabelOptions(controller.chart.data, intervalLabels(result.result)) : undefined

  return <Flex vertical gap="large" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
    <header>
      <Typography.Title level={2} style={{ margin: 0 }}>研究结果浏览</Typography.Title>
      <Typography.Paragraph type="secondary">逐层查看 Publication → Job → Analysis → ChartView。声明范围、执行状态与统计证据分别保留。</Typography.Paragraph>
      {staticMode && <Typography.Paragraph type="secondary" role="note" style={{ marginBottom: 0 }}>{sourceDisclosure ?? STATIC_EXPLORER_DISCLOSURE}</Typography.Paragraph>}
    </header>

    <Card title="Publications" extra={staticMode ? undefined : <Button onClick={() => controller.retryList?.()}>刷新</Button>}>
      {controller.list.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {controller.list.status === 'error' && <Space orientation="vertical">
        <ErrorState context="Publication 列表" error={controller.list.error} retry={controller.retryList} mode={mode} />
        {controller.page > 0 && <Button onClick={controller.previous}>上一页</Button>}
      </Space>}
      {controller.list.status === 'invalid' && <Alert type="error" title="静态 Publication 示例无效"
        description="嵌入的 Publication List、Manifest、Analysis、ChartView 或 ID 关联未通过正式契约校验，已拒绝展示；未执行在线请求。" showIcon />}
      {controller.list.status === 'success' && <>
        {controller.list.data.data.length === 0
          ? <Typography.Text>{staticMode
            ? controller.page === 0 ? '当前静态示例未嵌入 Publication；不代表在线 Publication Store 为空。' : '此静态示例页没有 Publication。'
            : controller.page === 0 ? 'Publication Store 为空。' : '此页没有 Publication。'}</Typography.Text>
          : <List rowKey="publication_id" dataSource={controller.list.data.data} renderItem={item => <List.Item actions={[
            <Button key="open" aria-pressed={controller.publication === item.publication_id}
              type={controller.publication === item.publication_id ? 'primary' : 'default'}
              onClick={() => controller.selectPublication(item.publication_id)}>选择</Button>,
          ]}><List.Item.Meta title={item.publication_id}
            description={<Tag>{staticMode ? '嵌入示例 · 发布状态：' : '发布状态：'}{item.status}</Tag>} /></List.Item>} />}
        <Flex gap="small" align="center" wrap>
          <Typography.Text type="secondary">当前第 {controller.page + 1} 页</Typography.Text>
          <Button disabled={!controller.canPrevious} onClick={controller.previous}>上一页</Button>
          <Button disabled={!controller.canNext} onClick={controller.next}>下一页</Button>
        </Flex>
        {staticMode && !controller.canNext && (controller.morePagesNotEmbedded
          ? <Alert type="info" title="后续页面未嵌入"
            description="此嵌入示例止于本页；该页仍声明可继续分页，因此在线 Publication Store 还有未嵌入的后续页面，不能视为在线列表的最后一页。" showIcon />
          : <Typography.Text type="secondary">该嵌入页未声明后续分页；这只描述嵌入集合的末端，不代表在线 Store 当前状态。</Typography.Text>)}
      </>}
    </Card>

    {controller.publication && <Card title="所选 Publication" extra={<Button onClick={() => controller.selectPublication(null)}>返回列表</Button>}>
      {controller.manifest.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {controller.manifest.status === 'error' && <ErrorState context="Publication" error={controller.manifest.error}
        retry={controller.retryManifest} mode={mode} />}
      {controller.manifest.status === 'missing' && <Alert type="warning" title="静态 Manifest 未嵌入"
        description="所选 Publication 在静态示例中没有对应的 Manifest；这不表示在线服务缺少该 Publication，也不会回退请求 HTTP。" showIcon />}
      {manifest && <Flex vertical gap="middle">
        <Typography.Text code>{manifest.publication_id}</Typography.Text>
        <Facts title="声明的 Research scope" data={{ status: manifest.status, metric: manifest.scope.metric, metric_parameters: manifest.scope.metric_parameters, subjects: manifest.scope.subjects, horizons: manifest.scope.horizons, inclusive_windows: manifest.scope.windows, analysis_requests: manifest.scope.analysis_requests, on_job_failure: manifest.scope.on_job_failure, jobs: manifest.jobs.length, analyses: manifest.analyses.length }} />
        <Collapse items={[{ key: 'source', label: 'Publication 来源证据', children: <>
          <Typography.Paragraph type="secondary">摘要与输入指纹用于标识证据，不证明市场数据真实性。</Typography.Paragraph>
          <Facts title="来源元数据" data={{ schema_version: manifest.schema_version, context: manifest.context, source_sha256: manifest.source.sha256, source_size: manifest.source.size }} />
          {staticMode && <Typography.Paragraph type="secondary" role="note">{STATIC_SOURCE_NOTE}</Typography.Paragraph>}
        </> }]} />
        <Typography.Title level={4}>Jobs 与 Analysis</Typography.Title>
        {manifest.jobs.map((job, index) => <Card key={JSON.stringify(job.job_identity)} size="small" title={`Job ${index + 1} — ${job.status}`}>
          <Flex gap="small" wrap><Typography.Text strong>{job.job_identity.subject}</Typography.Text><Typography.Text type="secondary">H = {job.job_identity.horizon} {job.job_identity.horizon_unit} · {job.job_identity.start_date} → {job.job_identity.end_date}</Typography.Text></Flex>
          <Collapse ghost size="small" items={[{ key: 'identity', label: '完整 Job 身份', children: <Facts title="Job 身份" data={job.job_identity} /> }]} />
          <List rowKey={id => id} dataSource={job.analyses} renderItem={id => {
            const item = manifest.analyses.find(a => a.analysis_id === id)
            return item ? <List.Item actions={[<Button key="select" aria-pressed={controller.analysis === id} type={controller.analysis === id ? 'primary' : 'default'} onClick={() => controller.selectAnalysis(id)}>选择 Analysis</Button>]}><List.Item.Meta title={`${item.request_id} — ${item.status}`} description={<span>Analysis ID: {id}<br />方法与参数： {JSON.stringify(item.spec)}<br />已发布 Views： {item.views.map(v => `${v.measure}: ${v.view_id}`).join(', ') || '无'}</span>} /></List.Item> : <List.Item>关联 Analysis 不可用：{id}</List.Item>
          }} />
        </Card>)}
      </Flex>}
    </Card>}

    {controller.analysis && <Card title="所选 Analysis" extra={<Button onClick={() => controller.selectAnalysis(null)}>关闭 Analysis</Button>}>
      {controller.result.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
      {controller.result.status === 'error' && <ErrorState context="Analysis" error={controller.result.error}
        retry={controller.retryResult} mode={mode} />}
      {controller.result.status === 'missing' && <Alert type="warning" title="静态 Analysis 未嵌入"
        description="所选 Analysis 在静态示例中没有对应的结果记录；这不表示在线服务缺少该 Analysis，也不会回退请求 HTTP。" showIcon />}
      {result && <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
        <Typography.Text code>{controller.analysis}</Typography.Text>
        <AnalysisDetails analysis={result} />
        <Typography.Title level={4}>ChartViews</Typography.Title>
        <Typography.Text type="secondary">选择一个已发布 View 后读取图表。</Typography.Text>
        {selected?.views.length ? <Space wrap>{selected.views.map(v => <Button key={v.view_id} title={v.view_id} aria-pressed={controller.view === v.view_id} type={controller.view === v.view_id ? 'primary' : 'default'} onClick={() => controller.setView(v.view_id)}>{v.measure}</Button>)}</Space> : <Alert type="info" title="没有可用的 ChartView" />}
        {controller.view && <Typography.Text code>View ID: {controller.view}</Typography.Text>}
        {controller.chart.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
        {controller.chart.status === 'error' && <ErrorState context="View" error={controller.chart.error}
          retry={controller.retryChart} mode={mode} />}
        {controller.chart.status === 'missing' && <Alert type="warning" title="静态 ChartView 未嵌入"
          description="所选 View 在静态示例中没有对应的 ChartView；这不表示在线服务缺少该 View，也不会回退请求 HTTP。" showIcon />}
        {controller.chart.status === 'success' && (unsupported
          ? <Alert type="warning" title="当前渲染器不支持此 View。" />
          : <div style={{ height: 450, minWidth: 0, width: '100%' }}><ChartView view={controller.chart.data} options={options} /></div>)}
      </Space>}
    </Card>}
  </Flex>
}
