import { Alert, Card, Collapse, Descriptions, Flex, Select, Table, Typography } from 'antd'
import { useMemo, useState } from 'react'
import { pairs, type Result } from '../api/validateResult'
import { metricLabels, number } from '../model/format'
import { historicalView, sessionDates } from '../model/charts'
import { ChartView, DateAxisControl, type DateAxisMode } from '../../../shared/visualization'
import { Histogram } from '../charts/Histogram'

const statusLabels = { empty_sample: '无有效历史样本', small_sample: '小样本，仅作描述', available: '统计可用', not_applicable: '当前观察不可用' }
export function RelativeValuePresentation({ result }: { result: Result }) {
  const [selected, setSelected] = useState(0)
  const [mode, setMode] = useState<DateAxisMode>('trading')
  const domain = useMemo(() => sessionDates(result), [result])
  const view = useMemo(() => historicalView(result, selected), [result, selected])
  const p = result.pairs[selected]
  const current = result.current_day.observations[selected]
  const all = p.distributions[3]
  return <Flex vertical gap="middle">
    <Card title="已提交的研究参数">
      <Descriptions items={[
        { key: 'product', label: 'Product', children: result.request.product_code },
        { key: 'start', label: 'History Start', children: result.request.history_start },
        { key: 'end', label: 'Evaluation Date', children: result.request.evaluation_date },
        { key: 'metric', label: 'Metric', children: metricLabels[result.metric] },
        { key: 'edges', label: 'Histogram Edges', children: result.request.histogram_edges ? JSON.stringify(result.request.histogram_edges) : '未请求' },
        { key: 'cutoff', label: 'Historical Cutoff（不含评价日）', children: result.historical_days.at(-1)?.trade_date ?? '无历史日期' },
      ]} />
      <Flex gap="small" align="center"><Typography.Text>Pair</Typography.Text><Select aria-label="Pair" value={selected} onChange={setSelected} options={pairs.map((label, value) => ({ label, value }))} style={{ width: 150 }} /></Flex>
    </Card>
    <Card title="当前价差相对于可比历史样本处于什么位置？">
      <Descriptions items={[
        { key: 'contracts', label: '当前真实合约', children: `${current?.near?.contract_code ?? '未提供'} / ${current?.far?.contract_code ?? '未提供'}` },
        { key: 'value', label: metricLabels[result.metric], children: number(current?.metrics?.[result.metric].value, result.unit === 'decimal_ratio') },
        { key: 'stage', label: 'Near DTE / Stage', children: `${number(current?.near_dte_days)} / ${current?.expiry_stage ?? '未提供'}` },
        { key: 'outcome', label: 'Outcome / Reason', children: current ? `${current.outcome} / ${current.reason ?? '—'}` : `closed / ${result.current_day.reason}` },
      ]} />
      <Flex gap="middle" wrap>{(['matching_stage', 'all_stages'] as const).map(kind => {
        const a = p[kind]; const d = p.distributions.find(d => d.stage === a.distribution_stage)
        return <Card key={kind} size="small" title={kind === 'matching_stage' ? '同到期阶段 · Matching-stage' : '全部阶段 · All-stages'} style={{ flex: '1 1 280px', minWidth: 0 }}>
          <Typography.Title level={3}>{a.percentile ? number(a.percentile.result.query_results[0].percentile, true) : '未提供百分位'}</Typography.Title>
          <Typography.Paragraph>{statusLabels[a.status]}（{a.status}） · N={d?.sample_count ?? '未提供'} · {a.distribution_stage ?? '无匹配阶段'}</Typography.Paragraph>
          {a.reason && <Typography.Paragraph>{a.reason}</Typography.Paragraph>}
          {a.status === 'small_sample' && <Alert type="warning" title="N=1–29：保留结果，仅作描述，不表示预测可靠性。" />}
          {a.percentile && <Typography.Paragraph type="secondary">当前历史百分位 · {a.percentile.result.estimator} · L/E/G={a.percentile.result.query_results[0].less_count}/{a.percentile.result.query_results[0].equal_count}/{a.percentile.result.query_results[0].greater_count}</Typography.Paragraph>}
        </Card>
      })}</Flex>
    </Card>
    <Card title="历史时间序列">
      <Flex vertical gap="middle">
        <DateAxisControl label="跨期价差时间轴" value={mode} onChange={setMode} />
        <Typography.Text type="secondary">真实合约切换及缺失观察处断开；价差水平变化不代表收益。评价日：{result.request.evaluation_date}（{result.current_day.status}）。</Typography.Text>
        <ChartView view={view} options={{ ordinalDates: mode === 'trading' ? domain : undefined }} />
      </Flex>
    </Card>
    <Card title="四组历史分布与 Quantile">
      <Table rowKey="stage" pagination={false} scroll={{ x: 1100 }} dataSource={p.distributions} columns={[
        { title: 'Stage', dataIndex: 'stage' }, { title: 'N', dataIndex: 'sample_count' },
        { title: '状态', render: (_, d) => `${statusLabels[d.status]} (${d.status})` },
        { title: '实际样本覆盖', render: (_, d) => d.sample_dates.length ? `${d.sample_dates[0]} – ${d.sample_dates.at(-1)}` : '无有效历史样本' },
        ...[0, .05, .25, .5, .75, .95, 1].map((q, index) => ({ title: `Q${q * 100}`, render: (_, d: typeof all) => number(d.quantile?.result.points_and_values[index][1], result.unit === 'decimal_ratio') })),
      ]} />
      <Typography.Paragraph type="secondary">Quantile 是历史分布的指标值；上方百分位是当前值的历史排名，两者不同。N 按有效 Pair-day 计数，不代表独立样本量。</Typography.Paragraph>
      {p.distributions.filter(d => d.status === 'small_sample').map(d => <Alert key={d.stage} type="warning" title={`${d.stage} · small_sample · N=${d.sample_count}，仅作描述。`} />)}
    </Card>
    {result.request.histogram_edges !== null && <Card title="显式边界 Histogram">{p.distributions.map(d => <section key={d.stage} aria-label={`${d.stage} Histogram`}>
      <Typography.Title level={4}>{d.stage}</Typography.Title>
      {d.histogram ? <><Histogram distribution={d} /><Typography.Paragraph>Underflow: {d.histogram.result.underflow_count}（{number(d.histogram.result.underflow_frequency, true)}）；Overflow: {d.histogram.result.overflow_count}（{number(d.histogram.result.overflow_frequency, true)}）</Typography.Paragraph></> : <Typography.Paragraph>empty_sample · N=0，无 Histogram 结果。</Typography.Paragraph>}
    </section>)}</Card>}
    <Collapse items={[
      { key: 'samples', label: `历史样本明细 · N=${all.sample_count}`, children: <Table rowKey="trade_date" pagination={{ pageSize: 10 }} scroll={{ x: 1100 }} dataSource={p.samples} columns={[
        { title: 'Trade Date', dataIndex: 'trade_date' }, { title: 'Metric value', render: (_, s) => number(s.metric.value, s.metric.unit === 'decimal_ratio') },
        { title: 'Stage', dataIndex: 'expiry_stage' },
        ...(['near', 'far'] as const).flatMap(side => [
          { title: `${side} contract`, render: (_, s: typeof p.samples[number]) => s[side].contract_code },
          { title: `${side} Close`, render: (_, s: typeof p.samples[number]) => number(s[side].close) },
          { title: `${side} Last Trading Date`, render: (_, s: typeof p.samples[number]) => s[side].delist_date },
        ]),
      ]} /> },
      { key: 'about', label: '样本解释与来源限制', children: <>
        <Typography.Paragraph>历史样本严格早于评价日。同到期阶段与全部阶段是独立比较；不会用全部阶段排名替代空的同阶段排名。empty_sample 没有排名；small_sample 保留结果；available 不意味着预测可靠。</Typography.Paragraph>
        <Typography.Paragraph>数据使用真实合约同日 Close 与最后交易日间隔。年化价差是价格关系，不代表实际收益率、等待价值、收益预测或交易指令，也不保证历史元数据为 point-in-time。</Typography.Paragraph>
        <Typography.Paragraph>历史候选 {result.historical_accounting.candidate_count} · 有效 {result.historical_accounting.valid_count} · 排除 {result.historical_accounting.excluded_count} · 不适用 {result.historical_accounting.not_applicable_count}</Typography.Paragraph>
        <Typography.Paragraph>{result.source_context.provider} / {result.source_context.exchange} / {result.source_context.price_field}</Typography.Paragraph>
        {result.source_context.limitations.map((text, i) => <Typography.Paragraph key={i}>{text}</Typography.Paragraph>)}
      </> },
    ]} />
  </Flex>
}
