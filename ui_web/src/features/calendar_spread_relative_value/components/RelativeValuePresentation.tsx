import { Alert, Card, Collapse, Descriptions, Flex, Select, Table, Typography } from 'antd'
import { useMemo, useState } from 'react'
import { pairs, type Result } from '../api/validateResult'
import { metricLabels, number, count, stageLabel, observationReason } from '../model/format'
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
  const coverage = (dates: string[]) => dates.length ? `${dates[0]} 至 ${dates.at(-1)}` : '无有效历史样本'
  return <Flex vertical gap="middle">
    <Typography.Paragraph>近月多头移至远月时，当前收盘价差关系相比历史上处于什么位置？比较同品种、同合约对和同一价差口径，不预测未来收益。</Typography.Paragraph>
    <Card title="当前价差相对于可比历史样本处于什么位置？">
      <Flex gap="small" align="center" wrap style={{ marginBottom: 16 }}><Typography.Text>合约对</Typography.Text><Select aria-label="合约对" value={selected} onChange={setSelected} options={pairs.map((label, value) => ({ label, value }))} style={{ width: 150 }} /></Flex>
      <Descriptions items={[
        { key: 'product', label: '品种', children: result.request.product_code },
        { key: 'end', label: '评价日期', children: result.request.evaluation_date },
        { key: 'contracts', label: '当前近月 / 远月合约', children: `${current?.near?.contract_code ?? '未提供'} / ${current?.far?.contract_code ?? '未提供'}` },
        { key: 'value', label: metricLabels[result.metric], children: number(current?.metrics?.[result.metric].value, result.unit === 'decimal_ratio') },
        { key: 'dte', label: '近月距最后交易日（自然日）', children: count(current?.near_dte_days) },
        { key: 'stage', label: '当前到期阶段', children: stageLabel(current?.expiry_stage) },
      ]} />
      {(!current || current.outcome !== 'valid') && <Alert type="info" showIcon title={observationReason(current?.reason ?? result.current_day.reason)} />}
      <Typography.Paragraph type="secondary">历史起点 {result.request.history_start}；历史截止 {result.historical_days.at(-1)?.trade_date ?? '无历史日期'}，不含评价日。数值越高，表示近月多头移至远月的收盘价关系相对更有利；年化价差率不是年收益率，也不代表实际移仓收益。</Typography.Paragraph>
      <Flex gap="middle" wrap>{(['matching_stage', 'all_stages'] as const).map(kind => {
        const a = p[kind]; const d = p.distributions.find(d => d.stage === a.distribution_stage)
        return <Card key={kind} size="small" title={kind === 'matching_stage' ? '同到期阶段的历史百分位' : '全部阶段的历史百分位'} style={{ flex: '1 1 280px', minWidth: 0 }}>
          <Typography.Title level={3}>{a.percentile ? number(a.percentile.result.query_results[0].percentile, true) : '无可用百分位'}</Typography.Title>
          <Typography.Paragraph>{statusLabels[a.status]} · 有效样本 N={d?.sample_count ?? '未提供'}</Typography.Paragraph>
          <Typography.Paragraph type="secondary">{stageLabel(a.distribution_stage)} · {coverage(d?.sample_dates ?? [])}</Typography.Paragraph>
          {a.status === 'empty_sample' && <Typography.Paragraph>该参考群体没有有效历史样本，不能计算当前排名。</Typography.Paragraph>}
          {a.status === 'not_applicable' && <Typography.Paragraph>当前观察不可用，保留历史分布，不提供当前排名。</Typography.Paragraph>}
          {a.status === 'small_sample' && <Alert type="warning" title="N=1–29：保留结果，仅作描述，不表示预测可靠性。" />}
        </Card>
      })}</Flex>
      <Typography.Paragraph style={{ marginTop: 16 }}>百分位是当前值在所选历史群体中的相对位置，按既定方法处理并列值。同阶段只比较近月剩余期限相近的样本；全部阶段纳入该合约对的所有到期阶段，因此排名可能不同，不能互相替代。</Typography.Paragraph>
      <Typography.Paragraph type="secondary">分位点数值（Quantile）是历史分布在指定位置的指标值；当前历史百分位（Percentile）是当前值的排名。N 是有效合约对交易日数，不代表独立样本量；统计可用不表示预测可靠。</Typography.Paragraph>
    </Card>
    {p.distributions.filter(d => d.status === 'small_sample' || d.status === 'empty_sample').map(d => <Alert key={d.stage} type={d.status === 'small_sample' ? 'warning' : 'info'} title={`${stageLabel(d.stage)} · ${statusLabels[d.status]} · N=${d.sample_count}${d.status === 'small_sample' ? '，仅作描述。' : '，无分位点数值。'}`} />)}
    <Card title="历史时间序列">
      <Flex vertical gap="middle">
        <DateAxisControl label="跨期价差时间轴" value={mode} onChange={setMode} />
        <Typography.Text type="secondary">真实合约切换及缺失观察处断开；价差水平变化不代表收益。评价日：{result.request.evaluation_date}（{result.current_day.status === 'open' ? '交易日' : '休市日'}）。</Typography.Text>
        <ChartView view={view} options={{ ordinalDates: mode === 'trading' ? domain : undefined }} />
      </Flex>
    </Card>
    <Collapse items={[
      { key: 'distributions', label: '四组历史分布与分位点数值（Quantile）', children: <Table rowKey="stage" pagination={false} scroll={{ x: 1100 }} dataSource={p.distributions} columns={[
        { title: '到期阶段', dataIndex: 'stage', render: stageLabel }, { title: '有效样本 N', dataIndex: 'sample_count' },
        { title: '状态', render: (_, d) => statusLabels[d.status] },
        { title: '实际样本覆盖', render: (_, d) => coverage(d.sample_dates) },
        ...[0, .05, .25, .5, .75, .95, 1].map((q, index) => ({ title: `${q * 100}% 分位值`, render: (_, d: typeof all) => number(d.quantile?.result.points_and_values[index][1], result.unit === 'decimal_ratio') })),
      ]} /> },
      ...(result.request.histogram_edges !== null ? [{ key: 'histogram', label: '显式边界直方图（Histogram）', children: <>{p.distributions.map(d => <section key={d.stage} aria-label={`${d.stage} Histogram`}>
        <Typography.Title level={4}>{stageLabel(d.stage)}</Typography.Title>
        {d.histogram ? <><Histogram distribution={d} /><Typography.Paragraph>低于边界：{d.histogram.result.underflow_count}（{number(d.histogram.result.underflow_frequency, true)}）；高于边界：{d.histogram.result.overflow_count}（{number(d.histogram.result.overflow_frequency, true)}）</Typography.Paragraph></> : <Typography.Paragraph>无有效历史样本（N=0），无直方图结果。</Typography.Paragraph>}
      </section>)}</> }] : []),
      { key: 'parameters', label: '研究参数与方法详情', children: <>
        <Descriptions items={[
          { key: 'metric', label: '价差口径', children: metricLabels[result.metric] },
          { key: 'edges', label: '直方图边界（原始单位）', children: result.request.histogram_edges ? JSON.stringify(result.request.histogram_edges) : '未请求' },
          { key: 'outcome', label: '原始当前状态 / 原因', children: current ? `${current.outcome} / ${current.reason ?? '—'}` : `closed / ${result.current_day.reason}` },
          { key: 'stage', label: '原始到期阶段', children: current?.expiry_stage ?? '未提供' },
        ]} />
        {(['matching_stage', 'all_stages'] as const).map(kind => {
          const a = p[kind]; const rank = a.percentile?.result.query_results[0]
          return <Typography.Paragraph key={kind}>{kind} · {a.status} · {a.reason ?? '—'} · {a.distribution_stage ?? '—'}{rank && <> · {a.percentile!.result.estimator} · L/E/G（低于 / 等于 / 高于当前值）={rank.less_count}/{rank.equal_count}/{rank.greater_count}</>}</Typography.Paragraph>
        })}
      </> },
      { key: 'samples', label: `历史样本明细 · N=${all.sample_count}`, children: <Table rowKey="trade_date" pagination={{ pageSize: 10 }} scroll={{ x: 1100 }} dataSource={p.samples} columns={[
        { title: '交易日', dataIndex: 'trade_date' }, { title: '指标值', render: (_, s) => number(s.metric.value, s.metric.unit === 'decimal_ratio') },
        { title: '到期阶段', dataIndex: 'expiry_stage', render: stageLabel },
        ...(['near', 'far'] as const).flatMap(side => [
          { title: `${side === 'near' ? '近月' : '远月'}合约`, render: (_, s: typeof p.samples[number]) => s[side].contract_code },
          { title: `${side === 'near' ? '近月' : '远月'}收盘价`, render: (_, s: typeof p.samples[number]) => number(s[side].close) },
          { title: `${side === 'near' ? '近月' : '远月'}最后交易日`, render: (_, s: typeof p.samples[number]) => s[side].delist_date },
        ]),
      ]} /> },
      { key: 'about', label: '样本解释与来源限制', children: <>
        <Typography.Paragraph>历史样本严格早于评价日。同到期阶段与全部阶段是独立比较；不会用全部阶段排名替代空的同阶段排名。无样本不提供排名，小样本保留结果，统计可用不意味着预测可靠。</Typography.Paragraph>
        <Typography.Paragraph>数据使用真实合约同日 Close 与最后交易日间隔。年化价差是价格关系，不代表实际收益率、等待价值、收益预测或交易指令，也不保证历史元数据为 point-in-time。</Typography.Paragraph>
        <Typography.Paragraph>历史候选 {result.historical_accounting.candidate_count} · 有效 {result.historical_accounting.valid_count} · 排除 {result.historical_accounting.excluded_count} · 不适用 {result.historical_accounting.not_applicable_count}</Typography.Paragraph>
        <Typography.Paragraph>{result.source_context.provider} / {result.source_context.exchange} / {result.source_context.price_field}</Typography.Paragraph>
        {result.source_context.limitations.map((text, i) => <Typography.Paragraph key={i}>{text}</Typography.Paragraph>)}
      </> },
    ]} />
  </Flex>
}
