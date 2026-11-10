import { formatUnit } from '../../../shared/format/unit'
import { intervalLabels } from '../../../shared/format/interval'
import { historyOptions, histogramOptions } from './presentation'
import { useState } from 'react'
import { Alert, Card, Collapse, Descriptions, Flex, Select, Segmented, Table, Tag, Typography, theme } from 'antd'
import { ChartView } from '../../../shared/visualization'
import type { Method, ReportData, Run } from './types'

const metrics = ['basis_value', 'basis_ratio', 'annualized_basis_ratio']
const sections = ['研究概览', '历史基差', '基差分布', '期限结构', '贴水持续区间', '证据与限制']
const text = (value: unknown) => value === undefined || value === null ? '不适用' : String(value)

function Methods({ methods }: { methods: Method[] }) {
  return <Flex vertical gap="small">{methods.map((m, i) => {
    const labels = m.result?.bins ? intervalLabels(m.result) : []
    return <Card key={i} size="small" title={m.spec.method}>
    {m.failure_category ? <Alert type={m.failure_category === 'no_eligible_sample' ? 'info' : 'error'} title={m.failure_category} description={m.reason} /> : m.result && <>
      <Typography.Paragraph>单位：{m.result.unit} · 有效样本数：{m.result.sample_count} · {m.result.estimator}</Typography.Paragraph>
      {m.spec.method === 'mean' && <Typography.Text>Mean：{formatUnit(m.result.value, m.result.unit)}</Typography.Text>}
      {m.result.points_and_values && <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="point" dataSource={m.result.points_and_values.map(([point, value]) => ({ point, value }))} columns={[{ title: 'Quantile Point', dataIndex: 'point' }, { title: '数值', dataIndex: 'value', render: value => formatUnit(value, m.result?.unit) }]} />}
      {m.result.bins && <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey="key" dataSource={[
        { key: 'underflow', interval: labels[0], count: m.result.underflow_count, frequency: m.result.underflow_frequency },
        ...m.result.bins.map((b, i) => ({ key: `bin-${i}`, interval: labels[i + 1], count: b.count, frequency: b.frequency })),
        { key: 'overflow', interval: labels.at(-1), count: m.result.overflow_count, frequency: m.result.overflow_frequency },
      ]} columns={[{ title: '区间（按单位展示）', dataIndex: 'interval' }, { title: 'IntervalCount', dataIndex: 'count' }, { title: 'Frequency（有效样本分母）', dataIndex: 'frequency', render: text }]} />}
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

export function Report({ data, mode }: { data: ReportData; mode: 'online' | 'offline' }) {
  const { token } = theme.useToken()
  const [metric, setMetric] = useState(metrics[0])
  const [slot, setSlot] = useState('M0')
  const [timeScale, setTimeScale] = useState('Trading Days')
  if (data.profile !== 'futures_basis_report_evidence_v1') throw new Error('Unsupported report version')
  const distribution = data.distributions.find(d => d.request.metric === metric && d.request.slot === slot)
  const obs = data.request.observation
  return <>
    <Flex vertical gap="large" style={{ width: '100%', minWidth: 0, maxWidth: 1400, margin: '0 auto' }}>
      <Typography.Title level={mode === 'offline' ? 1 : 3} style={{ margin: 0 }}>{mode === 'offline' ? `${obs.product_code} 历史基差研究报告` : '研究报告'}</Typography.Title>
      <Typography.Paragraph>{obs.product_code} · {obs.start_date} 至 {obs.end_date} · <Tag color={data.status === 'partial' ? 'orange' : 'blue'}>{data.status}</Tag></Typography.Paragraph>
      {data.status === 'partial' && <Alert showIcon type="warning" title="Partial：研究执行已完成；部分统计方法失败，原始失败证据保留在报告中。" />}
      <Flex component="nav" aria-label="报告章节" gap="middle" wrap style={{ paddingBlock: token.paddingSM }}>
        {sections.map((title, i) => <Typography.Link key={i} href={`#section-${i}`} onClick={event => { event.preventDefault(); document.getElementById(`section-${i}`)?.scrollIntoView({ block: 'start' }) }}>{String(i + 1).padStart(2, '0')} · {title}</Typography.Link>)}
      </Flex>
      <Card id="section-0" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>A. 研究概览</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Paragraph>{data.summary}</Typography.Paragraph>
        <Descriptions column={1} items={[
          { key: 'scope', label: '请求范围', children: `${obs.product_code} / ${obs.start_date}..${obs.end_date}` },
          { key: 'dates', label: 'CFFEX 候选交易日', children: `${data.candidate_dates.length}；${data.candidate_dates[0] ?? '无'}..${data.candidate_dates.at(-1) ?? '无'}` },
          { key: 'source', label: '数据来源', children: data.sources },
          { key: 'definition', label: '定义版本', children: data.definition_version },
          { key: 'fingerprint', label: '输入 SHA-256', children: <Typography.Text copyable>{data.fingerprint}</Typography.Text> },
        ]} />
        <Collapse items={[{ key: 'formulas', label: '指标定义与公式（Producer）', children: data.formulas.map(f => <Typography.Paragraph key={f}><Typography.Text code>{f}</Typography.Text></Typography.Paragraph>) }]} />
        <Typography.Title level={mode === 'offline' ? 3 : 5} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>各 Slot 统计均值</Typography.Title>
        <Table scroll={{ x: 'max-content' }} pagination={false} size="small" rowKey={r => r.request.analysis_id} dataSource={data.distributions} columns={[
          { title: 'Slot', render: (_, r) => r.request.slot }, { title: 'Metric', render: (_, r) => r.request.metric },
          { title: 'Mean / 状态', render: (_, r) => r.methods[0].failure_category ?? formatUnit(r.methods[0].result?.value, r.methods[0].result?.unit) },
          { title: '有效样本数', render: (_, r) => r.binding.length }, { title: '单位', render: (_, r) => r.methods[0].result?.unit ?? (r.request.histogram?.unit ?? '见证据') },
        ]} />
        <Typography.Title level={mode === 'offline' ? 3 : 5} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>数据完整性（各自单位，不相加）</Typography.Title>
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
      <Card id="section-1" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>B. 历史基差</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Paragraph>四个 Slot 是相对期限角色。合约转换由竖线和事件详情标注；缺失与转换断线。拖拽放大，工具栏切换 Pan、Reset；图例控制系列显示。decimal_ratio 以一位小数百分比展示；原始数据及证据单位保持不变。</Typography.Paragraph>
        <Segmented style={{ alignSelf: 'flex-start' }} aria-label="历史基差时间轴" value={timeScale} onChange={setTimeScale} options={['Trading Days', 'Calendar Days']} />
        {metrics.map(m => <div key={m} style={{ minWidth: 0, overflow: 'hidden' }}><ChartView view={data.views.history[m]} minPlotHeight={480} options={historyOptions(data.views.history[m], data.candidate_dates, timeScale === 'Trading Days', m === 'basis_value')} /></div>)}
      </Card>
      <Card id="section-2" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>C. 基差分布</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Text type="secondary">以下为本地展示设置，仅切换已有结果，不会提交请求或重新计算统计。</Typography.Text>
        <Flex gap="middle" wrap align="center"><Typography.Text>指标</Typography.Text><Select aria-label="Distribution metric" value={metric} onChange={setMetric} options={metrics.map(value => ({ value, label: value }))} style={{ minWidth: 260 }} /><Typography.Text>Slot</Typography.Text><Select aria-label="Distribution slot" value={slot} onChange={setSlot} options={['M0', 'M1', 'Q1', 'Q2'].map(value => ({ value, label: value }))} /></Flex>
        {distribution && <>
          <Typography.Paragraph>候选交易日：{distribution.candidates.length}；有效样本数：{distribution.binding.length}。分类柱等宽，不表示区间宽度或密度；区间边界及两侧外部区间全部保留。</Typography.Paragraph>
          {['count', 'frequency'].map(measure => {
            const view = data.views.histograms[`${distribution.request.analysis_id}/${measure}`]
            return view && <div key={measure} style={{ minWidth: 0, height: 340, overflow: 'hidden' }}><ChartView view={view} options={histogramOptions(view, distribution.methods.find(m => m.result?.bins)?.result)} /></div>
          })}
          <Methods methods={distribution.methods} />
        </>}
      </Card>
      <Card id="section-3" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>D. 期限结构</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
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
      <Card id="section-4" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>E. 贴水持续区间</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        <Typography.Title level={mode === 'offline' ? 3 : 5} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>完整段</Typography.Title><RunTable runs={data.persistence.flatMap(p => p.complete)} />
        <Typography.Title level={mode === 'offline' ? 3 : 5} style={{ margin: 0, fontSize: token.fontSizeHeading5 }}>被截断片段</Typography.Title>
        <Alert showIcon type="info" title="片段持续交易日数是已观测下界，不能作为完整持续期。window/gap 表示截断，只有 non_discount 证明完整边界。" />
        <RunTable runs={data.persistence.flatMap(p => p.censored)} />
      </Card>
      <Card id="section-5" title={<Typography.Title level={mode === 'offline' ? 2 : 4} style={{ margin: 0, fontSize: token.fontSizeHeading4, lineHeight: token.lineHeightHeading4 }}>F. 证据与限制</Typography.Title>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: token.padding, minWidth: 0 } }} style={{ scrollMarginTop: token.paddingLG }}>
        {data.runtime && <Collapse items={[{ key: 'runtime', label: '计算与渲染运行时', children: <Descriptions column={1} items={[
          { key: 'revision', label: '代码 revision', children: `${data.runtime.revision}${data.runtime.dirty ? '（有未提交改动，见证据上下文）' : ''}` },
          { key: 'python', label: '计算运行时', children: `Python ${data.runtime.python} / NumPy ${data.runtime.packages.numpy}` },
          { key: 'frontend', label: '渲染版本', children: `Node ${data.runtime.node} / React ${data.runtime.frontend_packages.react} / Plotly ${data.runtime.frontend_packages['plotly.js']}` },
        ]} /> }]} />}
        {data.limitations.map(l => <Typography.Paragraph key={l}>{l}</Typography.Paragraph>)}
        {mode === 'offline' ? <>
        <Typography.Paragraph>相邻 inputs.canonical.json 保留原始输入；evidence.json 保留完整观测、统计请求/结果与绑定；associations.json 和 views.json 保留图表关联。manifest.json / SHA256SUMS 可验证文件完整性。运行 REPRODUCE.md 中的 verify / replay，不依赖可变行情缓存。</Typography.Paragraph>
        <Collapse items={[{ key: 'details', label: '研究参数与逐日结果定位', children: <Typography.Paragraph>请求与统计方法参数见 evidence.json → science.request；Slot-day 和 Contract-day 见 science.observations；无效值原因见对应 metric outcome.reason。原始数值及单位保持不变，页面展示不重新计算任何研究指标。</Typography.Paragraph> }]} />
        </> : <Typography.Paragraph>在线报告提供当前请求、统计方法结果、Coverage、输入指纹与限制。完整离线证据包及 Verify / Replay 需独立本地生成；此 HTTP 接口不提供相邻证据文件。</Typography.Paragraph>}
        {mode === 'online' && <Collapse items={[{ key: 'request', label: 'Producer Report Request', children: <Typography.Paragraph><Typography.Text code>{JSON.stringify(data.request)}</Typography.Text></Typography.Paragraph> }]} />}
      </Card>
    </Flex>
  </>
}
