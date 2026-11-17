import { BIN_PRESETS, histogramAggregation, type BasisMetric } from '../model/histogramAggregation'
import { DistributionComparison } from '../charts/DistributionComparison'
import { distributionSummary } from '../model/basisPresentation'
import { formatUnit } from '../../../shared/format/unit'
import { formatPercent } from '../../../shared/format/number'
import { intervalLabels } from '../../../shared/format/interval'
import { historyOptions } from './presentation'
import { useMemo, useState } from 'react'
import { Alert, Card, Collapse, Descriptions, Flex, Select, Table, Tag, Typography, Button, theme } from 'antd'
import { ChartView, DateAxisControl, DEFAULT_DATE_AXIS_MODE, type DateAxisMode } from '../../../shared/visualization'
import type { Method, ReportData, Run } from './types'

const metrics = ['basis_value', 'basis_ratio', 'annualized_basis_ratio']
const metricLabels: Record<string, string> = { basis_value: '基差（点）', basis_ratio: '基差率（%）', annualized_basis_ratio: '年化基差率（%）' }
const sections = ['研究概览', '历史基差', '基差分布', '期限结构', '贴水持续区间', '证据与限制']

function Methods({ methods }: { methods: Method[] }) {
  return <Flex vertical gap="small">{methods.map((m, i) => {
    const labels = m.result?.bins ? intervalLabels(m.result) : []
    return <Card key={i} size="small" title={m.spec.method}>
    {m.failure_category ? <Alert type={m.failure_category === 'no_eligible_sample' ? 'info' : 'error'} title={m.failure_category} description={m.reason} /> : m.result && <>
      <Typography.Paragraph>单位：{m.result.unit} · 有效样本数：{m.result.sample_count} · {m.result.estimator}</Typography.Paragraph>
      {m.spec.method === 'mean' && <Typography.Text>Mean：{formatUnit(m.result.value, m.result.unit)}</Typography.Text>}
      {m.result.points_and_values && <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="point" dataSource={m.result.points_and_values.map(([point, value]) => ({ point, value }))} columns={[{ title: 'Quantile Point', dataIndex: 'point', render: value => formatPercent(value) }, { title: '数值', dataIndex: 'value', render: value => formatUnit(value, m.result?.unit) }]} />}
      {m.result.bins && <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="key" dataSource={[
        { key: 'underflow', interval: labels[0], count: m.result.underflow_count, frequency: m.result.underflow_frequency },
        ...m.result.bins.map((b, i) => ({ key: `bin-${i}`, interval: labels[i + 1], count: b.count, frequency: b.frequency })),
        { key: 'overflow', interval: labels.at(-1), count: m.result.overflow_count, frequency: m.result.overflow_frequency },
      ]} columns={[{ title: '区间（按单位展示）', dataIndex: 'interval' }, { title: 'IntervalCount', dataIndex: 'count' }, { title: 'Frequency（有效样本分母）', dataIndex: 'frequency', render: value => formatPercent(value) }]} />}
    </>}
  </Card>})}</Flex>
}

function RunTable({ runs }: { runs: Run[] }) {
  return <Table scroll={{ x: 'max-content' }} size="small" pagination={false} rowKey={r => `${r.slot}/${r.start}`} dataSource={runs} columns={[
    { title: 'Slot', dataIndex: 'slot' }, { title: '开始', dataIndex: 'start' }, { title: '结束', dataIndex: 'end' },
    { title: '持续交易日数', dataIndex: 'observed_trading_sessions' },
    { title: '左边界', dataIndex: 'left_boundary' }, { title: '右边界', dataIndex: 'right_boundary' },
    { title: '期间合约转换', render: (_, r) => r.transitions.length },
  ]} />
}

export function Report({ data, mode, sourceDisclosure, sectionNavigation = 'fragment' }: {
  sourceDisclosure?: string
  data: ReportData
  mode: 'online' | 'offline' | 'demo'
  /**
   * `fragment` keeps the standalone section links. Compact modes have no navigation. `local` scrolls without any
   * fragment or history change, so a hash-routed static page keeps its active route.
   */
  sectionNavigation?: 'fragment' | 'local'
}) {
  const { token } = theme.useToken()
  const [metric, setMetric] = useState<BasisMetric>('annualized_basis_ratio')
  const [width, setWidth] = useState<number>(BIN_PRESETS.annualized_basis_ratio.default)
  const projection = useMemo(() => histogramAggregation(data, metric, width), [data, metric, width])
  const [timeScale, setTimeScale] = useState<DateAxisMode>(DEFAULT_DATE_AXIS_MODE)
  const historyViews = useMemo(() => Object.fromEntries(metrics.map(metric => {
    const view = data.views.history[metric]
    return [metric, { ...view, layout: { ...view.layout, title: `历史${metricLabels[metric]}` } }]
  })), [data.views.history])
  if (data.profile !== 'futures_basis_report_evidence_v1') throw new Error('Unsupported report version')
  const obs = data.request.observation
  const sectionTitle = (title: string, index: number) => `${String(index + 1).padStart(2, '0')} · ${title}`
  const jump = (index: number) => document.getElementById(`section-${index}`)?.scrollIntoView({ block: 'start' })
  const historyCharts = <>
        <DateAxisControl label="历史基差时间轴" value={timeScale} onChange={setTimeScale} />
        {metrics.map(m => <div key={m}>
          {m === 'annualized_basis_ratio' && <Typography.Paragraph>合约到期日的剩余期限 D=0，年化基差按研究定义主动留空，并非行情数据错误；原始基差仍然保留。</Typography.Paragraph>}
          <div tabIndex={mode === 'demo' ? 0 : undefined} aria-label={mode === 'demo' ? `${metricLabels[m]} 图表，窄屏可横向滚动` : undefined} style={{ minWidth: 0, overflow: mode === 'demo' ? 'auto' : 'hidden' }}><div style={{ minWidth: mode === 'demo' ? 640 : undefined }}><ChartView view={historyViews[m]} minPlotHeight={480} options={{ ...historyOptions(data.views.history[m], data.candidate_dates, timeScale === 'trading', m === 'basis_value'),
          missingValuesDisclosure: { title: '无有效指标值日期', description: '包含合约到期、无有效合约或数据不可用等情况，具体原因见日期详情。' },
          dateEventsDisclosure: mode === 'offline' ? undefined : { description: '标记不同期限 Slot 所对应的期货合约发生切换的日期，仅用于描述合约映射变化，不代表实际交易。' } }} /></div></div></div>)}
  </>
  const distributionCharts = <>
        <Flex gap="middle" wrap align="center"><Typography.Text>指标</Typography.Text><Select aria-label="Distribution metric" value={metric} onChange={(value: BasisMetric) => { setMetric(value); setWidth(BIN_PRESETS[value].default) }} options={metrics.map(value => ({ value, label: metricLabels[value] }))} style={{ minWidth: 0, width: 260, maxWidth: '100%' }} /><Typography.Text>分箱宽度</Typography.Text><Select aria-label="Bin width" value={width} onChange={setWidth} options={BIN_PRESETS[metric].widths.map(value => ({ value, label: `${value} ${metric === 'basis_value' ? '点' : '个百分点'}` }))} style={{ minWidth: 145 }} /></Flex>
        {metric === 'annualized_basis_ratio' && <Typography.Paragraph>年化基差率用于比较不同到期期限下的基差强度，不等于实际持有收益；临近到期时数值可能较敏感。</Typography.Paragraph>}
        <Typography.Text type="secondary">本地仅进行展示性分箱，正式统计结果保持不变，不会提交请求或重新执行研究。</Typography.Text>
        {data.distributions.filter(d => d.request.metric === metric).flatMap(d => d.methods
          .filter(m => m.spec.method === 'interval_count' && m.failure_category && m.failure_category !== 'no_eligible_sample')
          .map((m, i) => <Alert key={`${d.request.analysis_id}/${i}`} type="warning" title={`${d.request.slot}：${m.failure_category}（Eligible N=${d.binding.length}）`} />))}
        <DistributionComparison projection={projection} metric={metric} width={width} />
        <section aria-label="统计摘要" style={{ minWidth: 0 }}>
          <Typography.Title level={5}>各 Slot 统计摘要</Typography.Title>
          <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="slot"
            dataSource={distributionSummary(data.distributions, metric)} columns={[
              { title: 'Slot', dataIndex: 'slot' }, { title: 'N', dataIndex: 'n' },
              { title: 'Min', dataIndex: 'min' }, { title: 'P25', dataIndex: 'p25' },
              { title: 'Median', dataIndex: 'median' }, { title: 'P75', dataIndex: 'p75' },
              { title: 'Max', dataIndex: 'max' }, { title: 'Mean', dataIndex: 'mean' },
            ]} />
        </section>
        {mode === 'offline' && <Collapse defaultActiveKey={data.distributions.filter(d => d.request.metric === metric).map(d => d.request.analysis_id)} items={data.distributions.filter(d => d.request.metric === metric).map(d => ({ key: d.request.analysis_id, label: `${d.request.slot} 正式统计方法`, children: <Methods methods={d.methods} /> }))} />}

  </>
  if (mode !== 'offline') return <Card data-testid="compact-report" title={<Typography.Title level={3} style={{ margin: 0 }}>研究报告</Typography.Title>}
    styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ minWidth: 0 }}>
    {data.status === 'partial' && <Alert showIcon type="warning" title="Partial：研究执行已完成，部分统计方法失败。" />}
    <Typography.Title level={4}>研究问题</Typography.Title>
    <Typography.Paragraph>{data.summary}</Typography.Paragraph>
    {mode === 'demo' && sourceDisclosure && <Collapse items={[{ key: 'source', label: '数据来源', children: <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>{sourceDisclosure}</Typography.Paragraph> }]} />}
    <Collapse items={[{ key: 'formulas', label: '指标定义与公式', children: data.formulas.map(formula => <Typography.Paragraph key={formula}><Typography.Text code>{formula}</Typography.Text></Typography.Paragraph>) }]} />
    <Typography.Title level={4}>研究可视化</Typography.Title>
    <section aria-label="历史基差" data-testid="history-charts" style={{ minWidth: 0 }}>
      <Typography.Title level={5}>历史基差</Typography.Title>{historyCharts}
    </section>
    <section aria-label="基差分布" style={{ minWidth: 0 }}>
      <Typography.Title level={5}>基差分布</Typography.Title>{distributionCharts}
    </section>
  </Card>
  return <>
    <Flex vertical gap="large" style={{ width: '100%', minWidth: 0, maxWidth: 1400, margin: '0 auto' }}>
      <Typography.Title level={1} style={{ margin: 0 }}>{mode === 'offline' ? `${obs.product_code} 历史基差研究报告` : '研究报告'}</Typography.Title>
      <Typography.Paragraph>{obs.product_code} · {obs.start_date} 至 {obs.end_date} · <Tag color={data.status === 'partial' ? 'orange' : 'default'}>{data.status}</Tag></Typography.Paragraph>
      {data.status === 'partial' && <Alert showIcon type="warning" title="Partial：研究执行已完成；部分统计方法失败，原始失败证据保留在报告中。" />}
      <Flex component="nav" aria-label="报告章节" gap="middle" wrap style={{ paddingBlock: token.paddingSM }}>
        {sections.map((title, i) => sectionNavigation === 'local'
          ? <Button key={i} type="link" style={{ padding: 0, height: 'auto' }} onClick={() => jump(i)}>{sectionTitle(title, i)}</Button>
          : <Typography.Link key={i} href={`#section-${i}`} onClick={event => { event.preventDefault(); jump(i) }}>{sectionTitle(title, i)}</Typography.Link>)}
      </Flex>
      <Card id="section-0" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>A. 研究概览</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Paragraph>{data.summary}</Typography.Paragraph>
        <Descriptions column={1} items={[
          { key: 'scope', label: '请求范围', children: `${obs.product_code} / ${obs.start_date}..${obs.end_date}` },
          { key: 'dates', label: 'CFFEX 候选交易日', children: `${data.candidate_dates.length}；${data.candidate_dates[0] ?? '无'}..${data.candidate_dates.at(-1) ?? '无'}` },
          { key: 'source', label: '数据来源', children: data.sources },
          { key: 'definition', label: '定义版本', children: data.definition_version },
          { key: 'fingerprint', label: '输入 SHA-256', children: <Typography.Text copyable>{data.fingerprint}</Typography.Text> },
        ]} />
        <Collapse items={[{ key: 'formulas', label: '指标定义与公式（Producer）', children: data.formulas.map(f => <Typography.Paragraph key={f}><Typography.Text code>{f}</Typography.Text></Typography.Paragraph>) }]} />
        <Typography.Title level={3} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>数据完整性（各自单位，不相加）</Typography.Title>
        <Table scroll={{ x: 'max-content' }} size="small" pagination={false} rowKey="dependency" dataSource={Object.entries(data.coverage).map(([dependency, coverage]) => ({ dependency, ...coverage }))} columns={[
          { title: '来源 / 单位', dataIndex: 'dependency', render: v => `${v} / ${v.startsWith('calendar') ? '自然日' : v === 'futures' ? '产品交易日' : '指数交易日'}` },
          { title: '请求', dataIndex: 'requested_units' }, { title: '成功', dataIndex: 'successful_units' },
          { title: '缺失', dataIndex: 'missing_units' }, { title: '待处理', dataIndex: 'pending_units' }, { title: '失败', dataIndex: 'failed_units' },
        ]} />
        <Collapse items={[{ key: 'eligibility', label: '逐 Slot / Metric 有效样本与不可用原因分类', children: <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey={r => `${r.slot}/${r.metric}`} dataSource={data.accounting} columns={[
          { title: 'Slot', dataIndex: 'slot' }, { title: 'Metric', dataIndex: 'metric' }, { title: '候选数', dataIndex: 'candidate_count' },
          ...['eligible', 'unavailable', 'excluded', 'not_applicable'].map(status => ({ title: status, render: (_: unknown, r: ReportData['accounting'][number]) => r.outcomes.find(o => o.status === status)?.identities.length })),
        ]} /> }]} />
      </Card>
      <Card id="section-1" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>B. 历史基差</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Paragraph>四个 Slot 是相对期限角色。合约转换由竖线和事件详情标注；缺失与转换断线。拖拽放大，工具栏切换 Pan、Reset；图例控制系列显示。比例以一位小数百分比展示，非整数点数以两位小数展示；原始数据及证据单位保持不变。</Typography.Paragraph>
        {historyCharts}
      </Card>
      <Card id="section-2" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>C. 基差分布</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        {distributionCharts}
      </Card>
      <Card id="section-3" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>D. 期限结构</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Paragraph>使用当前分布面板选择的 Metric：{metric}。每组两侧均只使用共同有效交易日，不代表 Calendar Spread。</Typography.Paragraph>
        <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey={r => r.request.analysis_id} dataSource={data.comparisons.filter(c => c.request.metric === metric)} columns={[
          { title: 'Slot Pair', render: (_, r) => r.request.slots?.join(' / ') },
          { title: '共同有效样本数', render: (_, r) => r.common_dates.length },
          { title: '未进入共同样本的日期数', render: (_, r) => r.dropped.length },
        ]} expandable={{ expandedRowRender: r => <Flex vertical gap="small">
          <Typography.Paragraph>共同日期：{r.common_dates.join(', ') || '无'}</Typography.Paragraph>
          <Typography.Title level={5}>{r.request.slots?.[0]}</Typography.Title><Methods methods={r.left_methods} />
          <Typography.Title level={5}>{r.request.slots?.[1]}</Typography.Title><Methods methods={r.right_methods} />
          <Typography.Title level={5}>逐日丢弃原因</Typography.Title>
          <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="date" dataSource={r.dropped_details} columns={[
            { title: '日期', dataIndex: 'date' }, { title: '左侧', render: (_, d) => `${d.left.slot}: ${d.left.outcome.status} ${d.left.outcome.reason ?? ''}` },
            { title: '右侧', render: (_, d) => `${d.right.slot}: ${d.right.outcome.status} ${d.right.outcome.reason ?? ''}` },
          ]} />
        </Flex> }} />
      </Card>
      <Card id="section-4" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>E. 贴水持续区间</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Title level={3} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>完整段</Typography.Title><RunTable runs={data.persistence.flatMap(p => p.complete)} />
        <Typography.Title level={3} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>被截断片段</Typography.Title>
        <Alert showIcon type="info" title="片段持续交易日数是已观测下界，不能作为完整持续期。window/gap 表示截断，只有 non_discount 证明完整边界。" />
        <RunTable runs={data.persistence.flatMap(p => p.censored)} />
      </Card>
      <Card id="section-5" title={<Typography.Title level={2} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>F. 证据与限制</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        {data.runtime && <Collapse items={[{ key: 'runtime', label: '计算与渲染运行时', children: <Descriptions column={1} items={[
          { key: 'revision', label: '代码 revision', children: `${data.runtime.revision}${data.runtime.dirty ? '（有未提交改动，见证据上下文）' : ''}` },
          { key: 'python', label: '计算运行时', children: `Python ${data.runtime.python} / NumPy ${data.runtime.packages.numpy}` },
          { key: 'frontend', label: '渲染版本', children: `Node ${data.runtime.node} / React ${data.runtime.frontend_packages.react} / Plotly ${data.runtime.frontend_packages['plotly.js']}` },
        ]} /> }]} />}
        {data.limitations.map(l => <Typography.Paragraph key={l}>{l}</Typography.Paragraph>)}

        <Typography.Paragraph>相邻 inputs.canonical.json 保留原始输入；evidence.json 保留完整观测、统计请求/结果与绑定；associations.json 和 views.json 保留图表关联。manifest.json / SHA256SUMS 可验证文件完整性。运行 REPRODUCE.md 中的 verify / replay，不依赖可变行情缓存。</Typography.Paragraph>
        <Collapse items={[{ key: 'details', label: '研究参数与逐日结果定位', children: <Typography.Paragraph>请求与统计方法参数见 evidence.json → science.request；Slot-day 和 Contract-day 见 science.observations；无效值原因见对应 metric outcome.reason。原始数值及单位保持不变，页面展示不重新计算任何研究指标。</Typography.Paragraph> }]} />

      </Card>
    </Flex>
  </>
}
